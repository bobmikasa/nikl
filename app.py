from flask import Flask, request, redirect, url_for, send_from_directory, render_template
import os
import requests
import re
from ipaddress import ip_address, IPv4Address

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

def get_asn(ip, token):
    try:
        if not isinstance(ip_address(ip), IPv4Address):
            return None
        url = f"https://ipinfo.io/{ip}/json?token={token}"
        response = requests.get(url)
        data = response.json()
        org = data.get('org', '')
        if org:
            return org.split()[0]
        return None
    except Exception as e:
        return None

def filter_ips(input_file, output_file, excluded_asns, token):
    tested_count = 0
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            tested_count += 1
            ip_match = re.search(r'@(.*?):', line)
            if ip_match:
                ip = ip_match.group(1)
                asn = get_asn(ip, token)
                if asn and asn not in excluded_asns:
                    outfile.write(line)
    return tested_count

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'list.txt')
        file.save(file_path)
        output_file = os.path.join(app.config['DOWNLOAD_FOLDER'], 'save.txt')
        excluded_asns = {'AS209242', 'AS13335'}
        api_token = 'bc24c39c83f539'
        count = filter_ips(file_path, output_file, excluded_asns, api_token)
        return render_template('index.html', count=count, download=True)
    return redirect(url_for('index'))

@app.route('/download')
def download_file():
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], 'save.txt', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
