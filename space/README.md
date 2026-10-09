---
title: RAG ANSSI
emoji: 🛡️
colorFrom: blue
colorTo: red
sdk: docker
app_port: 7860
pinned: false
short_description: Questions sur les guides de l'ANSSI, réponses citées
---

# Questions-réponses sur les guides de cybersécurité de l'ANSSI

Démonstration d'un RAG sur 45 guides de l'ANSSI : chaque phrase de la réponse cite sa source (guide, page),
et l'assistant répond « je ne sais pas » quand les guides ne contiennent pas la réponse. Les questions
passent par des garde-fous (détection d'injection de prompt, masquage des données personnelles).

Démo limitée en nombre de questions. Code, évaluation et résultats : {GITHUB_URL}

Guides publiés par l'ANSSI, réutilisés sous Licence Ouverte 2.0. Ce projet n'est ni affilié à l'ANSSI ni
approuvé par elle.
