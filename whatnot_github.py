"""
Version GitHub Actions : une seule verification par execution.
Le webhook Discord est lu dans la variable d'environnement DISCORD_WEBHOOK (secret GitHub).
"""
import os
import re
import sys
import requests

WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")
URL = "https://www.whatnot.com/fr-FR/user/anadoutoutdoux"
FICHIER_ETAT = "etat.txt"  # memorise les lives deja signales

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
}


def lives_en_cours(html):
    texte = html.replace('\\"', '"')
    trouves = []
    motif = (
        r'"__typename":"LiveStream","id":"([0-9a-f-]+)","activeViewers":(\d+)'
        r'.{0,1500}?"status":"([A-Z_]+)"'
    )
    for m in re.finditer(motif, texte):
        if m.group(3) == "PLAYING" and m.group(1) not in [t[0] for t in trouves]:
            trouves.append((m.group(1), int(m.group(2))))
    return trouves


def lire_etat():
    if os.path.exists(FICHIER_ETAT):
        with open(FICHIER_ETAT, encoding="utf-8") as f:
            return set(l.strip() for l in f if l.strip())
    return set()


def ecrire_etat(ids):
    with open(FICHIER_ETAT, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(ids)) + "\n")


def main():
    if not WEBHOOK:
        print("Erreur : secret DISCORD_WEBHOOK absent.")
        sys.exit(1)

    r = requests.get(URL, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        print(f"Page inaccessible (HTTP {r.status_code}) : Whatnot bloque probablement GitHub.")
        sys.exit(1)

    lives = lives_en_cours(r.text)
    print(f"Lives en cours : {len(lives)}")

    deja = lire_etat()
    for live_id, spectateurs in lives:
        if live_id not in deja:
            requests.post(
                WEBHOOK,
                json={"content": (
                    f"🔴 Live en cours ! ({spectateurs} spectateurs)\n"
                    f"https://www.whatnot.com/fr-FR/live/{live_id}\n"
                    f"Profil : {URL}"
                )},
                timeout=15,
            ).raise_for_status()
            deja.add(live_id)
            print("Alerte envoyee pour", live_id)

    ecrire_etat(deja)


if __name__ == "__main__":
    main()
