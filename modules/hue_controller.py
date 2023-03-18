import time
import json
import sqlite3
import requests
from typing import Optional
from dataclasses import dataclass

import streamlit as st
from huesdk import Hue
from huesdk import Discover


DATABASE_PATH = "./database/users.db"
IMAGE_PATH = "./img/hue_bridge.png"


@dataclass
class User:
    name: str = None
    key: str = None
    ip: str = None


class UserDatabase:
    def __init__(self):
        self.db = DATABASE_PATH

    def connect(self):
        self.conn = sqlite3.connect(self.db)
        self.curs = self.conn.cursor()
        self.curs.execute("create table if not exists users (name, key, ip)")

    def disconnect(self):
        self.conn.close()

    def get_user(self, name: Optional[str] = None) -> Optional[str]:
        self.connect()
        users = self.fetchall()
        for _name, _key, _ip in users:
            if name:
                if name == _name:
                    return User(_name, _key, _ip)
            else:
                return User(_name, _key, _ip)
        self.disconnect()
        return None

    def fetchall(self) -> tuple:
        self.curs.execute("SELECT * FROM users")
        users = self.curs.fetchall()
        return users

    def add_user(self, user: User):
        self.connect()
        self.curs.execute(
            "insert into users (name, key, ip) values (?,?,?)",
            (user.name, user.key, user.ip),
        )
        self.conn.commit()
        self.disconnect()


class HueUserRegister:
    def get_key(self, user: User):
        recieve = self.create_key(user.name, user.ip)
        for status, info in recieve.items():
            if status == "error":
                return False, None, info["description"]
            elif status == "success":
                return True, info["username"], None

    @staticmethod
    def create_key(name, ip):
        post_data = {"devicetype": f"Gesture#PC {name}"}
        response = requests.post(f"http://{ip}/api", json=post_data, verify=False)
        recieve_json = json.loads(response.text)
        return recieve_json[0]


class HueUserSettingsGuide:
    def __init__(self):
        self.user = User()
        self.searched_ip = ""
        self.step = 1

    def user_settings(self):
        print(self.step)
        self.step1_enter_name()
        if self.step == 2:
            self.step2_enter_ip()
        if self.step == 3:
            self.step3_push_bridge_link_btn()
        if self.step == 4:
            self.step4_push_connect_btn()
        if self.step == 5:
            return True
        return False

    def step1_enter_name(self):
        self.user.name = st.sidebar.text_input("User name")
        if self.user.name:
            self.step = 2

    def step2_enter_ip(self):
        self.user.ip = st.sidebar.text_input(
            "Bridge ip address",
            help="check https://discovery.meethue.com/",
            value=self.searched_ip,
            type="password",
        )
        if st.sidebar.button("Auto search"):
            self.searched_ip = self.auto_search_ip()
            st.experimental_rerun()
        if not self.user.ip == "":
            self.step = 3

    def step3_push_bridge_link_btn(self):
        st.sidebar.write("Press link button")
        st.sidebar.image(IMAGE_PATH)
        if st.sidebar.checkbox("pressed"):
            self.step = 4

    def step4_push_connect_btn(self):
        hue_register = HueUserRegister()
        if st.sidebar.button("connect", type="primary"):
            success, key, msg = hue_register.get_key(self.user)
            if success:
                self.user.key = key
                self.step = 5
            else:
                st.sidebar.write(msg)

    def auto_search_ip(self):
        discover = Discover()
        response = discover.find_hue_bridge()
        # response = requests.get("https://discovery.meethue.com/")
        recieve_json = response.json()[0]
        ip = recieve_json["internalipaddress"]
        return ip


class HueControlApp:
    def __init__(self):
        self.user = None
        self.db = UserDatabase()
        self.guide = HueUserSettingsGuide()
        self.hue = None

    def get_user(self):
        self.user = self.db.get_user()
        return self.user

    def guide_user_settings(self):
        complete = self.guide.user_settings()
        if complete:
            self.user = self.guide.user
            self.db.add_user(self.user)
        return self.user

    def get_hue(self):
        self.user = self.get_user()
        if not self.user:
            self.user = self.guide_user_settings()
            if self.user:
                with st.spinner(text="Connecting..."):
                    time.sleep(1)
                st.experimental_rerun()
        else:
            self.hue = Hue(bridge_ip=self.user.ip, username=self.user.key)
