__author__ = "Jeremy Nelson"
from . import app, harvest, cache

@app.template_filter('footer')
def get_footer(s):
    footer = cache.get('footer')
    if footer:
        return footer
    harvest()
    return cache.get('footer')

@app.template_filter('header')
def get_header(s):
    header = cache.get('header')
    if header:
        return header
    harvest()
    return cache.get('header')

@app.template_filter('scripts')
def get_scripts(s):
    scripts = cache.get('scripts')
    if scripts:
        return scripts
    harvest()
    return cache.get('scripts')

@app.template_filter('styles')
def get_styles(s):
    styles = cache.get('styles')
    if styles:
        return styles
    harvest()
    return cache.get('styles')

@app.template_filter('tabs')
def get_tabs(s):
    tabs = cache.get('tabs')
    if tabs:
        return tabs
    harvest()
    return cache.get('tabs')

