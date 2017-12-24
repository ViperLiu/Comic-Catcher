from selenium import webdriver
from bs4 import BeautifulSoup
from subprocess import call
from threading import Thread
import requests
import os, errno
import json


class Catcher:
    def __init__(self):
        self.broswer_path = None
        self.driver = None

    def create_download_dir(self, path):
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        return True

    def set_browser_path(self, path):
        self.broswer_path = str(path)
        self.driver = webdriver.PhantomJS(executable_path=str(path))
        return True

    def set_target_url(self, url):
        self.target_url = str(url)
        return True

    def parse(self, target_url):
        try:
            self.driver.get(target_url)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        except:
            print('Fail to parse '+target_url)
            return False
        return soup

    def get_all_episodes(self, soup):
        ep_list = []
        tmp = soup.find_all(id='info')
        tag_a_list = tmp[1].find_all('a')
        for i in range(len(tag_a_list)):
            ep_list.append('http://www.cartoonmad.com'+tag_a_list[i]['href'])
        return ep_list

    def parse_single_episode(self, ep_link):
        return self.parse(ep_link)

    def get_episodes_pics(self, soup):
        return soup.select('img[src*="cartoonmad"]')[0]['src']

    def get_episode_links(self, soup):
        return 'http://www.cartoonmad.com/comic/'+soup.select('img[src*="cartoonmad"]')[0].parent['href']

    def has_next_page(self, soup):
        next_page_link = soup.select('img[src*="cartoonmad"]')[0].parent['href']
        if next_page_link == 'thend.asp':
            return False
        else:
            return True

    def download_episode_pics(self, download_dir, episode_num, pic_links):
        download_dir += str(episode_num)+'/'
        self.create_download_dir(download_dir)
        pic_list = []
        print('Downloading episode '+str(episode_num))
        for i in range(len(pic_links)):
            file_name = download_dir+pic_links[i].split('/')[-2]+'-'+pic_links[i].split('/')[-1]
            r = requests.get(pic_links[i])
            pic_list.append(file_name)
            with open(file_name, 'wb') as outfile:
                outfile.write(r.content)
        self.build_json(pic_list, download_dir)
        print('Downloading episode '+str(episode_num)+' finished')

    def load_current_episode_num(self, download_dir):
        try:
            count_file = open(download_dir+'current_episode.txt','r')
        except:
            self.save_current_episode_num(0, download_dir)
            return 0
        current_episode_num = int(count_file.readline())
        count_file.close()
        return current_episode_num

    def save_current_episode_num(self, current_episode_num, download_dir):
        count_file = open(download_dir+'current_episode.txt','w')
        count_file.write(str(current_episode_num)+'\n')
        count_file.close()
        return True

    def build_json(self, pic_list, download_dir):
        json_file =  open(download_dir+'pic_list.json', 'w')
        json_file.write(json.dumps(pic_list))
        json_file.close()

    def build_comics_json(self, comics_list):
        json_file =  open('F:/漫畫/漫畫/comics_list.json', 'w')
        json_file.write(json.dumps(comics_list))
        json_file.close()

    def read_comic_list(self):
        comics_list = []
        try:
            json_data=open('F:/漫畫/漫畫/comics_list.json').read()
        except:
            self.build_comics_json(comics_list)
            return comics_list
        comics_list = json.loads(json_data)
        return comics_list

test = Catcher()
download_dir = 'F:/漫畫/漫畫/'
url = input('Input comic url on "www.cartoonmad.com" : ')
comic_name = input('Input comic name (this will create folder for download) : ')
download_dir += comic_name+'/'
if comic_name not in test.read_comic_list:
    test.create_download_dir(download_dir)
test.set_browser_path('F:/projects/python_catch/phantomjs-2.1.1-windows/phantomjs-2.1.1-windows/bin/phantomjs')

#get comics list from json
comics_list = test.read_comic_list()
comics_list.append(comic_name)
comics_list.sort()
#update comics list
test.build_comics_json(comics_list)

#get all episodes
soup = test.parse(url)
episodes = test.get_all_episodes(soup)

#load current episode number
current_episode_num = test.load_current_episode_num(download_dir)

for i in range(current_episode_num, len(episodes), 1):
    test.save_current_episode_num(i+1, download_dir)
    pic_links = []
    episode_soup = test.parse_single_episode(episodes[i])
    count = 1
    while True:
        print('Processing episode '+ str(i+1) +' picture '+ str(count))
        picture_link = test.get_episodes_pics(episode_soup)
        pic_links.append(picture_link)
        next_page_link = test.get_episode_links(episode_soup)
        if test.has_next_page(episode_soup) == False:
            break
        episode_soup = test.parse(next_page_link)
        count += 1

    t = Thread(target=test.download_episode_pics, args=(download_dir, str(i+1), pic_links,))
    t.start()
