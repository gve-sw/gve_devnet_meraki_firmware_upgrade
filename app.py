""" Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied. 
"""

# Import Section
from asyncore import write
from flask import Flask, render_template, request, url_for, redirect
from collections import defaultdict
import datetime
import requests
import json
from dotenv import load_dotenv
import os, csv
from meraki import DashboardAPI

# load all environment variables
load_dotenv()


# Global variables
app = Flask(__name__)

DEVICE_TYPES = ['appliance', 'camera', 'cellularGateway', 'switch', 'wireless', 'environmental']
SUCCESS = []
FAIL = []
CSV_UPLOADED = False

switch_versions = []
wireless_versions = []

## Methods

# Read data from json file
def getJson(filepath):
	with open(filepath, 'r') as f:
		json_content = json.loads(f.read())
		f.close()

	return json_content

# Write data to json file
def writeJson(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f)
    f.close()


## Routes
@app.route('/', methods=["GET", "POST"])
def overview():
    global switch_versions, wireless_versions
    apikey = getJson('settings.json')['apikey']
    settings = getJson('settings.json')
    if apikey == "":
        return redirect('/settings')
    m = DashboardAPI(apikey)

    orgs = []
    switch_versions = []
    wireless_versions = []
    for o in m.organizations.getOrganizations():
        networks = []
        templates = []
        url = f"https://api.meraki.com/api/v1/organizations/{o['id']}/networks"
        headers = {
            "Accept" : "application/json",
            "X-Cisco-Meraki-API-Key" : apikey
        }
        networks_list = requests.get(url, headers=headers).json()
        try: 
            for t in m.organizations.getOrganizationConfigTemplates(o['id']):
                upgrades = m.networks.getNetworkFirmwareUpgrades(t['id'])
                switch_version = "Not applicable"
                switch_stable = "Not applicable"
                if 'switch' in upgrades['products']:
                    switch_version = f"{upgrades['products']['switch']['currentVersion']['firmware']} ({upgrades['products']['switch']['currentVersion']['releaseType']})"
                    if switch_version not in switch_versions:
                        switch_versions += [switch_version]
                    switch_stable = "Not available"
                    for version in upgrades['products']['switch']['availableVersions']:
                        if version['releaseType'] == "beta":
                            switch_stable = f"{version['firmware']} (beta)"
                wireless_version = "Not applicable"
                wireless_stable = "Not applicable"
                if 'wireless' in upgrades['products']:
                    wireless_version = f"{upgrades['products']['wireless']['currentVersion']['firmware']} ({upgrades['products']['wireless']['currentVersion']['releaseType']})"
                    if wireless_version not in wireless_versions:
                        wireless_versions += [wireless_version]
                    wireless_stable = "Not available"
                    for version in upgrades['products']['wireless']['availableVersions']:
                        if version['releaseType'] == "stable":
                            wireless_stable = f"{version['firmware']} (stable)"
                templates += [{
                    "id" : t['id'],
                    "name" : t['name'],
                    "networks" : [],
                    "switch" : switch_version, 
                    "wireless" : wireless_version,
                    "switchbeta" : settings['switch'],
                    "wirelessstable" : settings['wireless'],
                    "checked" : False
                }]
        except:
            print('Broken org')
        for n in networks_list:
            if 'isBoundToConfigTemplate' in n:
                if not n['isBoundToConfigTemplate']:
                    try:
                        upgrades = m.networks.getNetworkFirmwareUpgrades(n['id'])

                        # Switch
                        try:
                            switch_version = f"{upgrades['products']['switch']['currentVersion']['firmware']} ({upgrades['products']['switch']['currentVersion']['releaseType']})"
                            if switch_version not in switch_versions:
                                switch_versions += [switch_version]
                            switch_flag = is_version_older(settings['switch'], switch_version)
                        except:
                            switch_version = "Not available"
                            switch_flag = True
                        
                        # Wireless
                        try:
                            wireless_version = f"{upgrades['products']['wireless']['currentVersion']['firmware']} ({upgrades['products']['wireless']['currentVersion']['releaseType']})"
                            if wireless_version not in wireless_versions:
                                wireless_versions += [wireless_version]
                            wireless_flag = is_version_older(settings['wireless'], wireless_version)
                        except:
                            wireless_version = "Not available"
                            wireless_flag = True

                        networks += [{
                            "name": n['name'], 
                            "id":n['id'], 
                            "switch" : switch_version, 
                            "wireless" : wireless_version,
                            "switchbeta" : switch_flag,
                            "wirelessstable" : wireless_flag,
                            "checked" : False
                        }]
                    except Exception as e:
                        print(e)
                        print('Broken network')
                else:
                    for t in templates: 
                        if n['configTemplateId'] == t['id']:
                            t['networks'] += [n]
        orgs += [{
            "name" : o['name'],
            "id" : o['id'],
            "networks" : networks,
            "templates" : templates
        }]

    writeJson('orgs.json', orgs)
    orgs = getJson('orgs.json')
    return render_template('overview.html', orgs=orgs)

#Index
@app.route('/index', methods=["GET", "POST"])
def index():
    global SUCCESS, FAIL, CSV_UPLOADED
    apikey = getJson('settings.json')['apikey']
    if apikey == "":
        return redirect('/settings')

    # Tab 1
    with open('uploaded.csv', 'r') as f:
        settings=getJson('settings.json')
        reader = csv.reader(f)
        networks_selected = []
        for id in reader:
            networks_selected += [id[0]]
        settings['networks'] = networks_selected
        writeJson('settings.json', settings)

    settings = getJson('settings.json')
    orgs = getJson('orgs.json')
    m = DashboardAPI(apikey)
    i = 0
    for o in orgs:
        j = 0
        for n in o['networks']:
            checked = False
            if n['id'] in settings['networks']:
                checked = True
            orgs[i]['networks'][j]['checked'] = checked
            j += 1
        i += 1
    writeJson('orgs.json', orgs)
    
    # Tab 2
    settings = getJson('settings.json')
    if request.method == "POST":
        selected = dict(request.form.lists())['network']
        settings['networks'] = selected
        writeJson('settings.json', settings)
    settings = getJson('settings.json')

    orgs = getJson('orgs.json')
    m = DashboardAPI(apikey)
    i = 0
    for o in orgs:
        j = 0
        for n in o['networks']:
            checked = False
            if n['id'] in settings['networks']:
                checked = True
            orgs[i]['networks'][j]['checked'] = checked
            j += 1
        j = 0
        for t in o['templates']:
            checked = False
            if t['id'] in settings['networks']:
                checked = True
            orgs[i]['templates'][j]['checked'] = checked
            j += 1
        i += 1
    writeJson('orgs.json', orgs)

    to_check = settings['networks']
    working = []
    not_working = []
    not_working_message = "Faulty upgrade window for networks:"
    firmwares = {}
    for n in to_check:
        try: 
            firmware = m.networks.getNetworkFirmwareUpgrades(n)
            working += [n]
            for d in firmware['products']:
                if d not in firmwares:
                    firmwares[d] = []
                firmwares[d] += firmware['products'][d]['availableVersions']
        except: 
            try:
                not_working += [m.networks.getNetwork(n)['name']]
                print(f"Faulty upgrade window for {n}")
            except:
                print('broken network')
    settings['networks'] = working
    writeJson('settings.json', settings)
    
    if len(working) > 1:
        for d in firmwares:
            new = []
            seen = []
            for v in firmwares[d]:
                if v['id'] in seen:
                    new += [v]
                else:
                    seen += [v['id']]
            firmwares[d] = new
    
    if len(SUCCESS)>0 or len(FAIL)>0:
        space = ', '
        fail = len(FAIL)>0
        success = len(SUCCESS)>0
        fail_message = "Firmware scheduling failed for the following networks: "
        for f in FAIL:
            fail_message += f"{f['network']} (Error message: {f['error']}) "
        return render_template('home.html', orgs=orgs, firmware=firmwares, alert=fail, success=success, f_message=fail_message, s_message=f"Firmware upgrade scheduling was succesful for the following networks: {space.join(SUCCESS)}.")
    
    else:
        not_working_alert = len(not_working)>0
        space = ', '
        return render_template('home.html', orgs=getJson('orgs.json'), firmware=firmwares, alert=False, success=False, n_alert=not_working_alert, not_working_message=f"{not_working_message} {space.join(not_working)}.")

#Settings
@app.route('/settings', methods=["GET", "POST"])
def settings():
    global switch_versions, wireless_versions
    if request.method == "POST":
        apikey = request.form.get('apikey')
        switch = request.form.get('switch_version')
        wireless = request.form.get('wireless_version')
        settings = getJson("settings.json")
        settings['apikey'] = apikey
        settings['switch'] = switch
        settings['wireless'] = wireless
        writeJson("settings.json", settings)
        return redirect('/')
    return render_template('settings.html', settings=getJson('settings.json'), switch_versions=switch_versions, wireless_versions=wireless_versions)

#Schedule
@app.route('/schedule', methods=["GET", "POST"])
def schedule():
    global SUCCESS, FAIL
    SUCCESS=[]
    FAIL = []
    upgrades = {}
    settings = getJson('settings.json')
    m = DashboardAPI(settings['apikey'])
    if request.method == "POST":
        for t in DEVICE_TYPES:
            try:
                id = dict(request.form.lists())[f"checkbox-version-{t}"][0]
                version = id.split('.')[1]
                upgrades[t] = version
            except:
                upgrades[t] = "no-version"
    responses = []

    date = request.form.get('your-date')
    hour = request.form.get('your-time')
    dateobject = datetime.datetime.strptime(f"{date}-{hour}", '%Y-%m-%d-%H:%M')
    datestring = datetime.datetime.strftime(dateobject, '%Y-%m-%dT%H:%M:00Z')

    print(f"NETWORKS: {settings['networks']}")
    for n in settings['networks']:
        old = m.networks.getNetworkFirmwareUpgrades(n)
        body = {
            "products" : {}
        }
        for t in DEVICE_TYPES:
            try:
                current_version = old['products'][t]['currentVersion']['id']
                if upgrades[t] != 'no-version' and not current_version == int(upgrades[t]):
                    body["products"][t] = {
                        "nextUpgrade": {
                            "time" : datestring,
                            "toVersion": { "id": upgrades[t] }
                        }
                    }
            except:
                print(f"Product type {t} not in network {n}")
        url = f"https://api.meraki.com/api/v1/networks/{n}/firmwareUpgrades"
        headers = {
            "Accept" : "application/json",
            "X-Cisco-Meraki-API-Key" : settings['apikey']
        }
        result = requests.put(url, headers=headers, json=body)
        if result.status_code == 200:
            try:
                responses += [m.networks.getNetwork(n)['name']]
            except:
                responses += [n]
        else:
            print('Error upgrading: ' + result.text)
            try:
                FAIL += [{
                    'network' : m.networks.getNetwork(n)['name'],
                    'error' : result.json()['errors'][0]
                }]
            except:
                FAIL += [{
                    'network' : n,
                    'error' : result.json()['errors'][0]
                }]
    SUCCESS = responses
    
    return redirect('/index')

@app.route("/extract-networks", methods=["GET","POST"])
def upload_file_function():
    global CSV_UPLOADED

    settings = getJson("settings.json")
    apikey = settings['apikey']
    uploaded_file = request.files
    file_dict = uploaded_file.to_dict()
    the_file = file_dict["file"]
    if not the_file.filename.lower().endswith('.csv'):
        return "Please upload a valid CSV format, or enter the API keys manually"
    with open('uploaded.csv', 'wb') as f:
        f.write(the_file.read())

    m = DashboardAPI(apikey)
    networks = []
    for o in m.organizations.getOrganizations():
        networks += m.organizations.getOrganizationNetworks(o['id'])

    networks_selected = []
    with open("uploaded.csv", "r") as f:
        r = csv.reader(f)
        for l in r:
            if (len(l) > 0):
                for n in networks:
                    if n['name'] == l[0]:
                        networks_selected += [n['id']]
    with open("uploaded.csv", "w") as f:
        w = csv.writer(f)
        for ns in networks_selected:
            w.writerow([ns])

    CSV_UPLOADED = True
    
    return "Read CSV file"

def is_version_older(base, new):
    digits_base = ""
    for i in base:
        if i.isnumeric():
            digits_base += i
    digits_new = ""
    for i in new:
        if i.isnumeric():
            digits_new += i
    while len(digits_base) > len(digits_new):
        digits_new += "0"
    while len(digits_new) > len(digits_base):
        digits_base += "0"
    return int(digits_base) > int(digits_new)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5555, debug=True)