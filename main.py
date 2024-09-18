import requests
import os
import re
import time
import json
from requests.exceptions import RequestException

def read_cookies(file_path):
    """Reads cookies from a file."""
    try:
        with open(file_path, 'r') as file:
            return file.read().splitlines()
    except FileNotFoundError:
        print(f'File Not Found! Please Enter Valid File: {file_path}')
        return None

def make_request(url, headers, cookie):
    """Makes a GET request with the given headers and cookie."""
    try:
        response = requests.get(url, headers=headers, cookies={'Cookie': cookie})
        return response.text
    except RequestException as e:
        print(f'[!] Error making request: {e}')
        return None

def extract_eaag_token(response):
    """Extracts the 'EAAG' token from a Facebook response."""
    if 'EAAG' in response:
        token_eaag = re.search(r'(EAAG\w+)', response)
        if token_eaag:
            return token_eaag.group(1)
    return None

def get_valid_cookies(cookies_data):
    """Finds valid cookies that contain 'EAAG' tokens."""
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Linux; Android 11; RMX2144 Build/RKQ1.201217.002; wv) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/103.0.5060.71 '
            'Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/375.1.0.28.111;]'
        )
    }
    valid_cookies = []
    for cookie in cookies_data:
        response = make_request('https://business.facebook.com/business_locations', headers, cookie)
        token_eaag = extract_eaag_token(response)
        if token_eaag:
            valid_cookies.append((cookie, token_eaag))
    return valid_cookies

def send_comment(id_post, commenter_name, comment, cookie, token_eaag):
    """Sends a comment to a Facebook post."""
    try:
        comment_with_name = f'{commenter_name}: {comment}'
        data = {'message': comment_with_name, 'access_token': token_eaag}
        response = requests.post(
            f'https://graph.facebook.com/{id_post}/comments/',
            data=data,
            cookies={'Cookie': cookie}
        ).json()
        
        current_time = time.strftime('%Y-%m-%d %I:%M:%S %p')
        
        if 'id' in response:
            print(f'Post id: {id_post}')
            print(f'  - Time: {current_time}')
            print(f'Comment sent: {comment_with_name}')
            return True
        else:
            print(f'[!] Status: Failure')
            print(f'Link: https://m.basic.facebook.com/{id_post}')
            print(f'Comments: {comment_with_name}\n')
            return False
    except RequestException as e:
        print(f'[!] Error making request: {e}')
        return False

def main():
    """Main function for the automated commenting script."""
    cookies_data = read_cookies('cookie.txt')
    if not cookies_data:
        return

    valid_cookies = get_valid_cookies(cookies_data)
    if not valid_cookies:
        print('[!] No valid cookie found. Exiting...')
        return

    id_post = int(open('post.txt').readline().strip())
    commenter_name = open('name.txt').readline().strip()
    delay = int(open('speed.txt').readline().strip())
    comments = open('file.txt', 'r').readlines()
    
    # Initialize cookie index
    cookie_index = 0

    while True:
        try:
            time.sleep(delay)
            comment = comments[0].strip()  # Take the first comment each time
            current_cookie, token_eaag = valid_cookies[cookie_index]
            
            success = send_comment(id_post, commenter_name, comment, current_cookie, token_eaag)

            # If comment sending fails, immediately switch to the next cookie
            if not success:
                cookie_index = (cookie_index + 1) % len(valid_cookies)
                print(f'Switching to cookie {cookie_index + 1}')
                continue  # Skip to the next iteration of the loop

            if success:
                comments.pop(0)  # Remove the comment from the list
                if not comments:  # If list is empty, reload
                    comments = open('file.txt', 'r').readlines()
                cookie_index = (cookie_index + 1) % len(valid_cookies)
        except Exception as e:
            print(f'[!] An unexpected error occurred: {e}')
            time.sleep(5.5)

if __name__ == '__main__':
    main()
