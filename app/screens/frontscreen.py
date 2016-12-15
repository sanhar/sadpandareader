from kivy.uix.screenmanager import Screen
import time
from kivy.properties import ListProperty, StringProperty, BooleanProperty
from kivy.properties import NumericProperty
from kivy.clock import Clock
from kivy.app import App
from kivy.network.urlrequest import UrlRequest
from kivy.lang import Builder
import urllib

from os import linesep
from functools import partial

# Self created components
from components.buttons import ThumbButton, AvatarSampleWidget

import json
from favouritescreen import FavouriteScreen
from settingsscreen import SettingsScreen

#to unescape gallery strings
from HTMLParser import HTMLParser

from BeautifulSoup import BeautifulSoup as BS

from models import Search, Filters, Gallery, GalleryTags

Builder.load_file("kv/frontscreen.kv")


class FrontScreen(Screen):

    gallery_thumbs = ListProperty([])
    gidlist = ListProperty([])
    searchword = StringProperty("")
    searchpage = NumericProperty(0)
    newstart = BooleanProperty(True)
    title = StringProperty("Front page")
    has_entered = False
    has_refreshed = True

    def __init__(self, **kwargs):
        super(FrontScreen, self).__init__(**kwargs)
        App.get_running_app().root.ids.sadpanda_screen_manager.add_widget(
            FavouriteScreen(name="favourite_screen"))
        App.get_running_app().root.ids.sadpanda_screen_manager.add_widget(
            SettingsScreen(name="settings_screen"))

    def on_enter(self):

        self.ids.galleryscroll.bind(scroll_y=self.check_scroll_y)
        db = App.get_running_app().db
        search = db.query(Search).order_by(Search.id.desc()).first()
        if search:
            if self.newstart is True:
                self.searchword = search.searchterm
                self.new_search()
                self.newstart = False
            else:
                if self.searchword == search.searchterm:
                    pass
                else:
                    self.searchword = search.searchterm
                    self.new_search()
        else:
            self.searchword = ""
            self.new_search()

    def new_search(self):
        self.ids.main_layout.clear_widgets()
        self.searchpage = 0

        self.gallery_thumbs = []

        Clock.schedule_once(self.populate_front)
        Clock.schedule_once(partial(self.entered, True))

    def entered(self, conditional, dt):
        self.has_entered = True

    def enter_gallery(self, instance):

        if not App.get_running_app(
        ).root.ids.sadpanda_screen_manager.has_screen(
                "gallery_preview_screen"):
            from screens.gallerypreviewscreen import GalleryPreviewScreen
            preview_screen = GalleryPreviewScreen(
                name="gallery_preview_screen")
            preview_screen.galleryinstance = instance
            App.get_running_app().root.ids.sadpanda_screen_manager.add_widget(
                preview_screen)
        else:
            preview_screen = App.get_running_app(
            ).root.ids.sadpanda_screen_manager.get_screen(
                "gallery_preview_screen")
            preview_screen.galleryinstance = instance
        App.get_running_app().root.next_screen("gallery_preview_screen")

    def check_scroll_y(self, instance, somethingelse):
        if self.has_refreshed == True:
            if self.ids.galleryscroll.scroll_y <= -0.02:
                self.populate_front()
                self.has_refreshed = False
            else:
                pass

    def populate_front(self, *largs):
        # filter store
        db = App.get_running_app().db
        filters = db.query(Filters).order_by(Filters.id.desc()).first()
        #filters = filterstore.get("filters")
        #filtertemp = filters["filters"]
        self.gidlist = []
        headers = {'User-agent': 'Mozilla/5.0',
                   "Cookie": "",
                   "Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        cookies = App.get_running_app().root.cookies
        headers["Cookie"] = cookies
        searchword = self.searchword
        page0searchurl = str(
            "http://" + App.get_running_app().root.baseurl + ".org/?" +
            "f_doujinshi=" + str(filters.doujinshi) + "&f_manga=" + str(
                filters.manga) + "&f_artistcg=" + str(filters.artistcg) +
            "&f_gamecg=" + str(filters.gamecg) + "&f_western=" + str(
                filters.western) + "&f_non-h=" + str(filters.nonh) +
            "&f_imageset=" + str(filters.imageset) + "&f_cosplay=" + str(
                filters.cosplay) + "&f_asianporn=" + str(filters.asianporn) +
            "&f_misc=" + str(filters.misc) + "&f_search=" + urllib.quote_plus(
                self.searchword) + "&f_apply=Apply+Filter")
        pagesearchurl = str(
            "http://" + App.get_running_app().root.baseurl + ".org/?" + "page="
            + str(self.searchpage) + "f_doujinshi=" + str(filters.doujinshi) +
            "&f_manga=" + str(filters.manga) + "&f_artistcg=" + str(
                filters.artistcg) + "&f_gamecg=" + str(filters.gamecg) +
            "&f_western=" + str(filters.western) + "&f_non-h=" + str(
                filters.nonh) + "&f_imageset=" + str(filters.imageset) +
            "&f_cosplay=" + str(filters.cosplay) + "&f_asianporn=" + str(
                filters.asianporn) + "&f_misc=" + str(
                    filters.misc) + "&f_search=" + urllib.quote_plus(
                        self.searchword) + "&f_apply=Apply+Filter")
        if self.searchpage == 0:
            req = UrlRequest(
                page0searchurl,
                on_success=self.got_result,
                on_error=self.got_failure,
                req_headers=headers,
                method="GET")
        else:
            req = UrlRequest(
                pagesearchurl, self.got_result, req_headers=headers)

        self.searchpage += 1
        # pure html of ehentai link

    def got_failure(self, req, r):
        print req
        print r

    def got_result(self, req, r):
        data = r

        soup = BS(data, fromEncoding='utf8')
        gallerylinks = []

        # grabs all the divs with class it5 which denotes the gallery on the
        # page
        for link in soup.findAll('div', {'class': 'it5'}):
            # grabs all the links, should only be gallery links as of 29th of
            # august 2015
            gallerylinks.append(link.find('a')["href"])

        for link in gallerylinks:
            splitlink = link.split('/')
            # grab the gallery token
            gtoken = splitlink[-2]
            # grab the gallery id
            gid = splitlink[-3]
            self.gidlist.append([gid, gtoken])

        headers = {
            "Content-type": "application/json",
            "Accept": "text/plain",
            'User-agent':
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
            "Cookie": ""
        }
        payload = {"method": "gdata", "gidlist": self.gidlist}
        cookies = App.get_running_app().root.cookies
        headers["Cookie"] = cookies

        self.grabthumbs(headers, payload, cookies)

    def grabthumbs(self, headers, payload, cookies, *largs):
        print headers["Cookie"]
        params = urllib.urlencode(payload)
        r = UrlRequest(
            "https://" + App.get_running_app().root.baseurl + ".org/api.php",
            on_success=self.thumbgrab,
            req_body=json.dumps(payload),
            req_headers=headers)

    def thumbgrab(self, req, r):
        requestdump = r
        requestdump.rstrip(linesep)
        requestjson = json.loads(requestdump)
        i = 0
        try:
            for gallery in requestjson["gmetadata"]:
                self.add_button(gallery)
                i += 1
        except:
            pass

    def add_button(self, gallery, *largs):
        escapedtitle = gallery["title"]
        unescapedtitle = HTMLParser().unescape(escapedtitle)

        gallerybutton = ThumbButton(
            #gallerysource=gallery["thumb"],
            gallery_id=str(gallery["gid"]),
            gallery_token=str(gallery["token"]),
            pagecount=int(gallery["filecount"]),
            gallery_name=unescapedtitle,
            gallery_tags=gallery["tags"],
            gallery_thumb=gallery["thumb"],
            filesize=gallery["filesize"],
            category=gallery["category"],
            size_hint_x=1, )
        gallerybutton.bind(on_release=self.enter_gallery)
        gallerybutton.add_widget(AvatarSampleWidget(source=gallery["thumb"]))
        self.ids.main_layout.add_widget(gallerybutton)
        self.has_refreshed = True
