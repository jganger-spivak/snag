#!/bin/python3
import mechanicalsoup
import argparse
from pathlib import Path
from time import sleep
import urllib.parse
import subprocess

def crawl(base_url: str) -> list:
    print(f"Crawling {base_url}...")
    browser = mechanicalsoup.StatefulBrowser()
    browser.open(base_url)
    found_files = []
    for link in browser.links():
        anchor = link.get('href')
        if anchor == '../' or anchor == './' or anchor == "Parent Directory": # don't do a path traversal, try not to get stuck
            continue
        if '?' in anchor: # try to avoid non-file links
            continue
        if anchor[-1] == '/': 
            # print(f"Directory: {anchor}")
            found_files.extend(crawl(browser.url+anchor))
        else:
            # print(f"File: {anchor}")
            found_files.append(browser.url+anchor)
    browser.close()
    return found_files

def trim_urls(url_list: list, args: argparse.Namespace):
    to_trim = []
    for url in url_list:
        split_url = urllib.parse.urlsplit(url) # remove non-path part of URL
        filename = split_url[2] # get filepath from URL
        # if args.flatten:
        filename = filename.split("/")[-1] # if flattened, remove path except filename
        filename = urllib.parse.unquote(filename[0:]) # parse the HTTP escape codes
        # else:
        # filename = urllib.parse.unquote(filename[1:]) # parse the HTTP escape codes
        # print(f"Parsed filename: {filename}")
        root_path = Path(args.dir)
        file_path = root_path / Path(filename)
        file_path_partial = root_path / Path(filename + ".aria2")
        if file_path.exists() and not file_path_partial.exists():
            to_trim.append(url)
        if file_path.suffix == args.ignore_extension:
            to_trim.append(url)
    for url in to_trim:
        url_list.remove(url)

def download(args: argparse.Namespace):
    url_list = crawl(args.base_url)
    trim_urls(url_list, args)
    print("######## Results ########")
    print("URLS to download: ")
    aria2_cmd = f"aria2c --max-download-limit {args.max_download_limit} -j {args.max_concurrent_downloads} -d {args.dir} -Z "
    for url in url_list:
        aria2_cmd += f'"{url}" '
        print(url)
    good_to_go = input("Good to continue? y/N: ")
    if good_to_go.lower() != 'y':
        exit()
    
    # print(aria2_cmd)
    subprocess.call(aria2_cmd, shell=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="snag", description="Downloads all files from a webserver using aria2")
    parser.add_argument("base_url", type=str, help="The base URL to download from")
    parser.add_argument("-j", "--max-concurrent-downloads", type=int, default=1, help="How many simultaneous connections to use (default 1)")
    parser.add_argument("-d", "--dir", type=str, default='.', help="What directory should files be saved in? (default current dir)")
    parser.add_argument("--max-download-limit", type=int, default=2000000, help="Maximum bandwidth per connection (default ~2MB/s)")
    parser.add_argument("--ignore-extension", type=str, default="", help="Ignore files with this extension")
    parser.add_argument("--flatten", type=bool, default=False, help="UNUSED: Whether to flatten the file structure and place all downloaded files in one folder (default false)")
    args = parser.parse_args()
    download(args)