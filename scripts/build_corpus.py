"""Construit data/corpus.csv à partir de data/candidats.csv et de la sélection ci-dessous.

La sélection est écrite dans le code (et non faite à la main dans un tableur)
pour qu'elle soit relue en pull request et rejouable à l'identique.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATS_CSV = ROOT / "data" / "candidats.csv"
CORPUS_CSV = ROOT / "data" / "corpus.csv"

# slug du catalogue -> (doc_ref court et stable, thème)
# Une ligne par guide, même longue : la table se relit mieux ainsi.
SELECTION = {
    # Administration et architecture des SI
    "recommandations-relatives-ladministration-securisee-des-si": ("admin-securisee-si", "administration"),
    "usage-securise-dopenssh": ("openssh", "administration"),
    "recommandations-pour-ladministration-securisee-des-si-reposant-sur-ad": ("admin-ad", "administration"),
    "recommandations-de-securite-relatives-active-directory": ("active-directory", "administration"),
    "architecture-securisee-de-si": ("architecture-si", "administration"),
    "recommandations-pour-les-architectures-des-si-sensibles-ou-dr": ("archi-si-sensibles", "administration"),
    "recommandations-relatives-linterconnexion-dun-si-internet": (
        "interconnexion-internet",
        "administration",
    ),
    "cartographie-du-systeme-dinformation": ("cartographie-si", "administration"),
    "recommandations-de-securite-relatives-un-systeme-gnulinux": ("gnu-linux", "administration"),
    "mise-en-oeuvre-securisee-dun-serveur-windows": ("serveur-windows", "administration"),
    "recommandations-pour-la-mise-en-place-de-cloisonnement-systeme": (
        "cloisonnement-systeme",
        "administration",
    ),
    "guide-dhygiene-informatique": ("hygiene-informatique", "administration"),
    "la-tele-assistance-securisee": ("tele-assistance", "administration"),
    "fondamentaux-poste-multi-environnements": ("poste-multi-env", "administration"),
    # Authentification, identité et cryptographie
    "recommandations-relatives-lauthentification-multifacteur-et-aux-mots-de-passe": (
        "auth-mfa-mdp",
        "authentification",
    ),
    "recommandations-pour-la-securisation-de-la-mise-en-oeuvre-du-protocole-openid-connect": (
        "openid-connect",
        "authentification",
    ),
    "recommandations-de-securite-relatives-tls": ("tls", "authentification"),
    "infrastructure-de-gestion-de-cles-igc": ("igc", "authentification"),
    "mecanismes-cryptographiques": ("mecanismes-crypto", "authentification"),
    "automatisation-de-la-gestion-des-certificats-avec-acme": ("acme", "authentification"),
    "recommandations-de-deploiement-du-protocole-8021x": ("8021x", "authentification"),
    "recommandations-de-securite-relatives-ipsec": ("ipsec", "authentification"),
    "modele-zero-trust": ("zero-trust", "authentification"),
    "recommandations-sur-le-nomadisme-numerique": ("nomadisme", "authentification"),
    # Cloud, conteneurs, virtualisation
    "recommandations-de-securite-relatives-au-deploiement-de-conteneurs-docker": (
        "guide-conteneurs",
        "conteneurs",
    ),
    "recommandations-pour-lhebergement-des-si-sensibles-dans-le-cloud": ("cloud-si-sensibles", "conteneurs"),
    "virtualisation": ("virtualisation", "conteneurs"),
    "securisation-dune-infrastructure-vmware": ("vmware", "conteneurs"),
    "recommandations-de-deploiement-dun-service-iaas-openstack-secnumcloud": ("openstack", "conteneurs"),
    "devsecops": ("devsecops", "conteneurs"),
    "recommandations-de-securite-pour-un-systeme-dia-generative": ("ia-generative", "conteneurs"),
    "bases-de-donnees-relationnelles": ("bases-de-donnees", "conteneurs"),
    "securiser-un-site-web": ("site-web", "conteneurs"),
    "mise-en-oeuvre-securisee-dun-cms": ("cms", "conteneurs"),
    # Journalisation, supervision et réponse à incident
    "recommandations-de-securite-pour-larchitecture-dun-systeme-de-journalisation": (
        "journalisation",
        "journalisation",
    ),
    "securiser-la-journalisation-dans-un-environnement-microsoft-active-directory": (
        "journalisation-ad",
        "journalisation",
    ),
    "investigation-qualification-incidents": ("investigation-incidents", "journalisation"),
    "la-supervision-de-securite-les-cles-de-decision": ("supervision-decision", "journalisation"),
    "la-supervision-de-securite-piloter-un-projet-de-supervision": ("supervision-projet", "journalisation"),
    "cyberattaques-et-remediation-les-cles-de-decision": ("remediation-decision", "journalisation"),
    "cyberattaques-et-remediation-piloter-la-remediation": ("remediation-pilotage", "journalisation"),
    "cyberattaques-et-remediation-la-remediation-du-tier-0-active-directory": (
        "remediation-tier0-ad",
        "journalisation",
    ),
    "sauvegarde-des-systemes-dinformation": ("sauvegarde-si", "journalisation"),
    "attaques-par-rancongiciels-tous-concernes": ("rancongiciels", "journalisation"),
    "crise-cyber-les-cles-dune-gestion-operationnelle-et-strategique": ("crise-cyber", "journalisation"),
}


def main() -> None:
    with open(CANDIDATS_CSV, encoding="utf-8", newline="") as f:
        candidats = {row["slug"]: row for row in csv.DictReader(f)}

    missing = [slug for slug in SELECTION if slug not in candidats]
    if missing:
        raise SystemExit(f"Slugs absents du catalogue : {missing}")

    rows = []
    for slug, (doc_ref, theme) in SELECTION.items():
        c = candidats[slug]
        rows.append(
            {
                "doc_ref": doc_ref,
                "titre": c["titre"],
                "theme": theme,
                "url": c["url"],
                "date_maj": c["date_maj"],
            }
        )

    with open(CORPUS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["doc_ref", "titre", "theme", "url", "date_maj"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} guides écrits dans {CORPUS_CSV}")


if __name__ == "__main__":
    main()
