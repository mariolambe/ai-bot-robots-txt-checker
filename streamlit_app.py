import streamlit as st
import requests
import threading
from queue import Queue
import pandas as pd
import re
import matplotlib.pyplot as plt

# URL to fetch the list of AI bots
BOTS_URL = "https://raw.githubusercontent.com/ai-robots-txt/ai.robots.txt/main/robots.txt"
GITHUB_URL = "https://github.com/ai-robots-txt/ai.robots.txt/blob/main/robots.txt"

# Headers to mimic a legitimate browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}

# Function to fetch the list of AI bots
def fetch_ai_bots(url):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        bots = re.findall(r'User-agent: (\S+)', response.text)
        return bots
    else:
        return []

# Function to check robots.txt for selected bot disallow
def check_robots_txt(queue, disallowed_domains, allowed_domains, lock, bot, progress_queue):
    while not queue.empty():
        domain = queue.get()
        url = f"https://{domain}/robots.txt"
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                content = response.text.lower()
                if f"user-agent: {bot.lower()}" in content:
                    with lock:
                        disallowed_domains.append(domain)
                else:
                    with lock:
                        allowed_domains.append(domain)
            else:
                with lock:
                    allowed_domains.append(domain)
        except requests.exceptions.RequestException:
            with lock:
                allowed_domains.append(domain)  # Treat as allowed if there is an error
        finally:
            queue.task_done()
            progress_queue.put(1)

# Pre-filled domain lists based on country
domain_lists = {
    "Italy": [
    "zalando.it", "google.it", "amazon.it",
    "repubblica.it", "corriere.it", "poste.it", "gazzetta.it",
    "sky.it", "libero.it", "ilmeteo.it", "mediaset.it",
    "ilfattoquotidiano.it", "fanpage.it", "ansa.it", "ilmessaggero.it",
    "rainews.it", "subito.it", "virgilio.it", "diretta.it",
    "lastampa.it", "raiplay.it", "aruba.it", "ebay.it",
    "tim.it", "giallozafferano.it", "ilgazzettino.it", "tripadvisor.it",
    "ilgiornale.it", "immobiliare.it", "agenziaentrate.gov.it",
    "autoscout24.it", "trivago.it", "subito.it",
    "idealista.it", "kataweb.it", "ilmessaggero.it", "fanpage.it",
    "ilmessaggero.it", "ilgiornale.it", "libero.it", "gazzetta.it",
    "corriere.it", "repubblica.it", "ansa.it", "rainews.it",
    "ilfattoquotidiano.it", "mediaset.it", "posta.it", "ilmessaggero.it"
    ],
    "Germany": [
    "google.de", "amazon.de", "immobilienscout24.de", "spiegel.de", "bild.de", "t-online.de",
    "web.de", "gmx.net", "freenet.de", "ebay.de", "chip.de", "focus.de", "merkur.de",
    "rtl.de", "sat1.de", "prosieben.de", "golem.de", "heise.de", "tripadvisor.de",
    "ebay-kleinanzeigen.de", "gutefrage.net", "ardmediathek.de", "zdf.de", "tagesschau.de",
    "welt.de", "n-tv.de", "kicker.de", "sportschau.de", "sport1.de", "auto-motor-und-sport.de",
    "chefkoch.de", "netdoktor.de", "zeit.de", "sueddeutsche.de", "faz.net", "stern.de",
    "handelsblatt.com", "rp-online.de", "dw.com", "br.de", "ndr.de", "swp.de",
    "kaufda.de", "meinestadt.de", "quoka.de", "autoscout24.de", "holidaycheck.de", "immowelt.de",
    "apotheken-umschau.de", "finanzen.net"
    ],
    "France": [
    "google.fr", "amazon.fr", "lefigaro.fr", "lemonde.fr", "orange.fr",
    "free.fr", "laposte.fr", "leparisien.fr", "ebay.fr", "ouest-france.fr", "20minutes.fr",
    "rtl.fr", "lci.fr", "doctissimo.fr", "marmiton.org", "tripadvisor.fr", "leboncoin.fr",
    "allocine.fr", "sfr.fr", "pagesjaunes.fr", "francetvinfo.fr", "francetelevisions.fr",
    "tf1.fr", "larepubliquedespyrenees.fr", "lindependant.fr", "ladepeche.fr", "lamontagne.fr",
    "estrepublicain.fr", "dna.fr", "lexpress.fr", "mediapart.fr", "lesechos.fr", 
    "nouvelobs.com", "liberation.fr", "humanite.fr", "cnews.fr", "meteo.fr", "societe.com",
    "lequipe.fr", "franceinfo.fr", "lepoint.fr", "challenges.fr", "rue89.fr", "marianne.net",
    "midilibre.fr", "leberry.fr", "lamontagne.fr"
    ],
    "UK": [
           "google.co.uk", "amazon.co.uk", "bbc.co.uk", "dailymail.co.uk",
    "thesun.co.uk", "ebay.co.uk", "independent.co.uk", "telegraph.co.uk", "mirror.co.uk",
    "express.co.uk", "metro.co.uk", "thesun.co.uk", "tripadvisor.co.uk", "rightmove.co.uk",
    "zoopla.co.uk", "argos.co.uk", "currys.co.uk", "next.co.uk", "houseoffraser.co.uk",
    "very.co.uk", "game.co.uk", "pcworld.co.uk", "primark.co.uk", "moneysavingexpert.co.uk",
    "sainsburys.co.uk", "waitrose.co.uk", "aldi.co.uk", "lidls.co.uk", "tesco.co.uk",
    "asda.co.uk", "coop.co.uk", "morrisons.co.uk", "marksandspencer.com", "sky.com",
    "bt.com", "johnlewis.com", "asos.com", "debenhams.com", "sportsdirect.com",
    "game.co.uk", "pcworld.co.uk", "virginmedia.com", "lastminute.com", "thomascook.com",
    "bbc.com", "itv.com", "channel4.com"
    ],
    "US": [
        "google.com", "youtube.com", "facebook.com", "amazon.com", "reddit.com", "yahoo.com",
        "x.com", "instagram.com", "wikipedia.org", "linkedin.com", "ebay.com", "office.com",
        "walmart.com", "microsoftonline.com", "cnn.com", "netflix.com", "weather.com", "bing.com",
        "duckduckgo.com", "fandom.com", "zillow.com", "espn.com", "nytimes.com", "quora.com",
        "pornhub.com", "usps.com", "tiktok.com", "twitter.com", "chatgpt.com", "live.com",
        "foxnews.com", "twitch.tv", "paypal.com", "aol.com", "xvideos.com", "msn.com",
        "pinterest.com", "roblox.com", "etsy.com", "microsoft.com", "homedepot.com", "zoom.us",
        "sharepoint.com", "chaturbate.com", "chase.com", "indeed.com", "imdb.com", "hulu.com",
        "nextdoor.com", "discord.com"
    ]
}

# Streamlit app
def main():
    st.set_page_config(page_title="AI Bot Robots.txt Checker", layout="wide")

    st.title("AI Bot Robots.txt Checker")
    st.write("This app checks if domains disallow a specific AI bot in their `robots.txt` file.")
    st.write(f"This tool uses the list of AI bots from the [GitHub page]({GITHUB_URL}) to fetch the latest AI bots.")

    ai_bots = fetch_ai_bots(BOTS_URL)
    selected_bot = st.selectbox("Select an AI bot to check:", ai_bots)
    selected_country = st.selectbox("Select a country for pre-filled domains: (Optional)", ["None", "Italy", "Germany", "France", "UK", "US"])

    with st.form(key='check_domains_form'):
        if selected_country != "None":
            domains_input = st.text_area("Enter one domain per line (e.g., amazon.com, ebay.com):", "\n".join(domain_lists[selected_country]))
        else:
            domains_input = st.text_area("Enter one domain per line (e.g., amazon.com, ebay.com):")

        submit_button = st.form_submit_button(label='Check Domains')

    if submit_button:
        if domains_input:
            domains = [domain.strip() for domain in domains_input.split("\n") if domain.strip()]
            
            queue = Queue()
            disallowed_domains = []
            allowed_domains = []
            lock = threading.Lock()
            progress_queue = Queue()

            for domain in domains:
                queue.put(domain)

            total_domains = len(domains)
            threads = []
            for _ in range(10):  # Adjust the number of threads as needed
                thread = threading.Thread(target=check_robots_txt, args=(queue, disallowed_domains, allowed_domains, lock, selected_bot, progress_queue))
                thread.start()
                threads.append(thread)

            progress_bar = st.progress(0)
            completed_domains = 0

            while completed_domains < total_domains:
                progress_queue.get()
                completed_domains += 1
                progress_bar.progress(completed_domains / total_domains)

            queue.join()
            for thread in threads:
                thread.join()

            st.success("Check complete!")
            col1, col2 = st.columns(2)

            def make_clickable(df, col):
                df[col] = df[col].apply(lambda x: f'<a href="https://{x}/robots.txt" target="_blank">{x}</a>')
                return df

            with col1:
                st.subheader(f"Domains Blocking {selected_bot}:")
                if disallowed_domains:
                    df_disallowed = pd.DataFrame(disallowed_domains, columns=["Domain"], index=range(1, len(disallowed_domains) + 1))
                    df_disallowed = make_clickable(df_disallowed, 'Domain')
                    st.markdown(df_disallowed.to_html(escape=False), unsafe_allow_html=True)
                else:
                    st.write(f"No domains are blocking {selected_bot}.")

            with col2:
                st.subheader(f"Domains Allowing {selected_bot}:")
                if allowed_domains:
                    df_allowed = pd.DataFrame(allowed_domains, columns=["Domain"], index=range(1, len(allowed_domains) + 1))
                    df_allowed = make_clickable(df_allowed, 'Domain')
                    st.markdown(df_allowed.to_html(escape=False), unsafe_allow_html=True)
                else:
                    st.write(f"No domains are explicitly allowing {selected_bot}.")

            # Display statistics
            st.subheader("Statistics")
            st.write(f"Total domains checked: {total_domains}")
            st.write(f"Domains blocking {selected_bot}: {len(disallowed_domains)} ({len(disallowed_domains)/total_domains*100:.2f}%)")
            st.write(f"Domains allowing {selected_bot}: {len(allowed_domains)} ({len(allowed_domains)/total_domains*100:.2f}%)")

            # Graphical representation
            st.subheader("Graphical Representation")
            labels = ['Blocked', 'Allowed']
            sizes = [len(disallowed_domains), len(allowed_domains)]
            colors = ['#ff9999','#66b3ff']
            fig1, ax1 = plt.subplots()
            ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.axis('equal')
            st.pyplot(fig1)

    # Footer with contact information
    st.markdown("""
        <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: white;
            color: black;
            text-align: center;
            padding: 10px;
            border-top: 1px solid #eaeaea;
        }
        </style>
        <div class="footer">
            <p>For ideas or feedback, contact me at <a href="mailto:your-email@example.com">your-email@example.com</a> or connect with me on <a href="https://www.linkedin.com/in/your-linkedin-profile" target="_blank">LinkedIn</a>.</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
