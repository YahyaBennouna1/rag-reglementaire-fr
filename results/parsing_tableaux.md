# Mesure du parsing des tableaux : Docling contre PyMuPDF

20 tableaux tirés au hasard (graine 42) parmi 240 tableaux d'au moins 3 lignes de données.
Pour chaque tableau : la sortie est-elle **lisible et complète** (lignes et colonnes justes) ?

| # | Guide | Page | Docling | PyMuPDF | Remarque |
|---|---|---|---|---|---|
| 1 | nomadisme | 36 | ✅ | ✅ | Règles numérotées ; il reste une césure (« res- treindre »), corrigée au nettoyage |
| 2 | admin-ad | 87 | ✅ | ✅ | Cellules sur 2 lignes, mais « Non » marque la fin de chaque ligne |
| 3 | active-directory | 1 | ✅ | ❌ | PyMuPDF : on ne sait pas à quel rôle appartient chaque ✓ |
| 4 | openstack | 77 | ✅ | ✅ | Liste des recommandations ; quelques mots collés chez Docling (« unmécanisme ») |
| 5 | cartographie-si | 40 | ❌ | ❌ | Cellules fusionnées : la granularité est décalée d'une ligne chez Docling, flottante chez PyMuPDF |
| 6 | cartographie-si | 3 | ✅ | ❌ | Sommaire : PyMuPDF sépare tous les titres de leurs numéros de page |
| 7 | auth-mfa-mdp | 13 | ✅ | ❌ | PyMuPDF : impossible de savoir où finit la menace et où commence la contre-mesure |
| 8 | admin-ad | 151 | ✅ | ✅ | Acronymes sur une ligne : les deux sont lisibles |
| 9 | openstack | 73 | ✅ | ❌ | PyMuPDF colle le champ et le début de sa valeur sur la même ligne |
| 10 | admin-ad | 15 | ✅ | ✅ | Le numéro de Tier sépare clairement les lignes |
| 11 | openssh | 2 | ✅ | ✅ | Petit tableau des versions |
| 12 | tls | 51 | ✅ | ✅ | Codes et suites TLS, une valeur par ligne |
| 13 | journalisation-ad | 77 | ✅ | ✅ | Les noms de paramètres (LogFile, MaxItems…) séparent les lignes |
| 14 | active-directory | 47 | ✅ | ✅ | Les noms de privilèges (Se…Privilege) séparent les lignes |
| 15 | mecanismes-crypto | 51 | ❌ | ❌ | Les deux perdent les exposants : « 215 » au lieu de 2^15 |
| 16 | guide-conteneurs | 18 | ✅ | ❌ | PyMuPDF : plusieurs numéros CIS par recommandation, lignes ambiguës |
| 17 | active-directory | 4 | ❌ | ✅ | Sommaire détecté comme tableau : Docling mélange les colonnes |
| 18 | active-directory | 3 | ❌ | ✅ | Sommaire détecté comme tableau : Docling mélange les colonnes |
| 19 | admin-ad | 4 | ❌ | ✅ | Sommaire détecté comme tableau : Docling mélange les colonnes |
| 20 | archi-si-sensibles | 107 | ✅ | ✅ | Liste des recommandations |

## Résultat

| | Docling | PyMuPDF |
|---|---|---|
| **Les 20 tableaux** | **15 / 20** | **13 / 20** |
| **Vrais tableaux de données** (sans les 4 sommaires) | **14 / 16** | **10 / 16** |

**Analyse :**
- Sur les **vrais tableaux de données**, Docling garde la structure (une ligne = une ligne du tableau) là où PyMuPDF rend un texte à plat, souvent ambigu dès qu'une cellule tient sur plusieurs lignes.
- **3 des 5 échecs de Docling sont des sommaires** (tableaux 17, 18, 19) que son modèle a pris pour des tableaux. Ce ne sont pas des données utiles : ils sont désormais **retirés au nettoyage** (règle « points de conduite »).
- Les **cellules fusionnées** (tableau 5) et les **exposants** (tableau 15) restent des limites, pour les deux outils.

**Méthode :** 20 tableaux tirés au hasard (graine 42) ; critère : peut-on reconstruire chaque ligne sans ambiguïté ? Première évaluation faite avec l'aide d'un assistant IA, **à confirmer par une relecture humaine**.

---

## Tableau 1 — nomadisme, page 36

### Docling

|   ID | Règle                                                                                                                                                                                                                                                       |
|------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|    1 | Les services hors-tunnel sont identifiés formellement et validés par les responsables de la sécurité de l'entité.                                                                                                                                           |
|    2 | Les flux hors-tunnel sont protégés en confidentialité et sont authentifiés par des protocoles configurés à l'état de l'art (p. ex. en suivant le guide TLS [24] pour des flux HTTPS).                                                                       |
|    3 | Les flux hors-tunnel doivent être filtrés en sortie sur le pare-feu local avec une liste d'adresses IP publiques restreinte au strict besoin opérationnel.                                                                                                  |
|    4 | Le filtrage des flux hors-tunnel doit être fait par adresses IP (ou éventuellement par noms de domaine DNS) plutôt que par plages d'adresses IP (en fonction des préconisations de l'éditeur).                                                              |
|    5 | Le suivi des règles de filtrage local sur le poste nomade doit être le plus régulier possible et tenir compte des modifications des adresses IP publiques et des ports réseaux des services hors-tunnel.                                                    |
|    6 | Si le fournisseur d'un service hors-tunnel permet la configuration d'un proxy, cette fonction doit être activée afin de res- treindre les adresses IP publiques de destination autorisées en sortie à ce seul proxy.                                        |
|    7 | Si le fournisseur le propose, la phase d'authentification des utilisateurs aux services hors-tunnel doit transiter au travers du tunnel VPN et seuls les flux de données applicatives doivent transiter hors-tunnel une fois l'utilisateur authentifié 20 . |
|    8 | Les fournisseurs des services hors-tunnel doivent proposer un niveau de journalisation aligné avec celui requis par la poli- tique de sécurité de l'entité.                                                                                                 |
|    9 | Toute modification non prévue de la configuration du split-tunneling (règles de filtrage, table de routage, client VPN) sur un poste nomade doit systématiquement déclencher la remontée d'une alerte aux administrateurs de sécurité de l'entité.          |
|   10 | La route par défaut de la table de routage du poste nomade est l'adresse IP du concentrateur VPN. Les routes spécifiques des services hors-tunnel sont déclarées explicitement dans la table de routage.                                                    |

### PyMuPDF (texte brut de la même zone)

```
ID
Règle
1
Les services hors-tunnel sont identifiés formellement et validés par les responsables de la sécurité de l’entité.
2
Les flux hors-tunnel sont protégés en confidentialité et sont authentifiés par des protocoles configurés à l’état de l’art
(p. ex. en suivant le guide TLS [24] pour des flux HTTPS).
3
Les flux hors-tunnel doivent être filtrés en sortie sur le pare-feu local avec une liste d’adresses IP publiques restreinte au
strict besoin opérationnel.
4
Le filtrage des flux hors-tunnel doit être fait par adresses IP (ou éventuellement par noms de domaine DNS) plutôt que par
plages d’adresses IP (en fonction des préconisations de l’éditeur).
5
Le suivi des règles de filtrage local sur le poste nomade doit être le plus régulier possible et tenir compte des modifications
des adresses IP publiques et des ports réseaux des services hors-tunnel.
6
Si le fournisseur d’un service hors-tunnel permet la configuration d’un proxy, cette fonction doit être activée afin de res-
treindre les adresses IP publiques de destination autorisées en sortie à ce seul proxy.
7
Si le fournisseur le propose, la phase d’authentification des utilisateurs aux services hors-tunnel doit transiter au travers du
tunnel VPN et seuls les flux de données applicatives doivent transiter hors-tunnel une fois l’utilisateur authentifié 20.
8
Les fournisseurs des services hors-tunnel doivent proposer un niveau de journalisation aligné avec celui requis par la poli-
tique de sécurité de l’entité.
9
Toute modification non prévue de la configuration du split-tunneling (règles de filtrage, table de routage, client VPN) sur un
poste nomade doit systématiquement déclencher la remontée d’une alerte aux administrateurs de sécurité de l’entité.
10
La route par défaut de la table de routage du poste nomade est l’adresse IP du concentrateur VPN. Les routes spécifiques
des services hors-tunnel sont déclarées explicitement dans la table de routage.
```

## Tableau 2 — admin-ad, page 87

### Docling

| Méthode de connexion distante                                                                        | Dissémination de secret réutilisable?   |
|------------------------------------------------------------------------------------------------------|-----------------------------------------|
| Ouverture de session interactive par RDP avec l'option restricted admin (RDP RA) b                   | Non                                     |
| Authentification Windows intégrée e à des services par le réseau                                     | Non                                     |
| PowerShell WinRM avec le protocole d'authentification par défaut (c'est à dire par Kerberos ou NTLM) | Non                                     |
| PsExec avec credentials implicites (c'est-à-dire sans utiliser le commuta- teur « -u utilisateur »)  | Non                                     |
| Commandes NET USE                                                                                    | Non                                     |
| Appels RPC (par l'utilisation des composants logiciels enfichables de la MMC notamment)              | Non                                     |
| Registre à distance                                                                                  | Non                                     |

### PyMuPDF (texte brut de la même zone)

```
Méthode de connexion distante
Dissémination de
secret réutilisable?
Ouverture de session interactive par RDP avec l’option restricted admin
(RDP RA)b
Non
Authentification Windows intégréee à des services par le réseau
Non
PowerShell WinRM avec le protocole d’authentification par défaut (c’est
à dire par Kerberos ou NTLM)
Non
PsExec avec credentials implicites (c’est-à-dire sans utiliser le commuta-
teur « -u utilisateur »)
Non
Commandes NET USE
Non
Appels RPC (par l’utilisation des composants logiciels enfichables de la
MMC notamment)
Non
Registre à distance
Non
```

## Tableau 3 — active-directory, page 1

### Docling

| Développeur    |    |
|----------------|----|
| Administrateur | ✓  |
| RSSI           | ✓  |
| DSI            |    |
| Utilisateur    |    |

### PyMuPDF (texte brut de la même zone)

```
Développeur
Administrateur
✓
RSSI
✓
DSI
Utilisateur
```

## Tableau 4 — openstack, page 77

### Docling

| R1   | Configurer keystone pour utiliser un annuaire LDAP                                                            |   16 |
|------|---------------------------------------------------------------------------------------------------------------|------|
| R2   | Utiliser plusieurs domaines et des annuaires LDAP dédiés par domaine                                          |   16 |
| R3   | Utiliser des ports TCP distincts pour les points d'entrée admin et public des services                        |   19 |
| R4   | Placer les APIs public et admin sur des réseaux distincts                                                     |   20 |
| R5   | Mettre en place un serveur mandataire inverse en amont des APIs à destination des com- manditaires            |   20 |
| R6   | Mettre en place un filtrage applicatif en amont des APIs                                                      |   22 |
| R7   | Mettre en place unmécanisme de de bloquage des jetons adminpour les APIs à destination des commanditaires     |   23 |
| R8   | Mettre en place unmécanisme de de bloquage des jetons public pour les APIs à destination du prestataire       |   24 |
| R9   | Mettre en place une authentificationmutuelle entre le client OPENSTACK et le serveurman- dataire              |   28 |
| R10  | Mettre en place un contrôle de cohérence entre le certificat X.509 et l'identité utilisateur                  |   28 |
| R11  | Mémoriser les paires constituées du champ DN des certificats X.509 et des jetons émis par le service keystone |   29 |
| R12  | Vérifier les associations de jetons envoyés par les clients OPENSTACK et des certificats X.509 utilisés       |   29 |
| R13  | Activer le chiffrement des volumes du service nova                                                            |   32 |
| R14  | Activer le chiffrement du stockage du service swift                                                           |   32 |
| R15  | Activer le chiffrement des échanges entre les services swift et glance                                        |   32 |
| R16  | Activer le chiffrement des échanges entre les services glance et nova                                         |   32 |
| R17  | Protéger les clés de chiffrement                                                                              |   33 |
| R18  | Configurer le chiffrement TLS à l'état de l'art pour les APIs des services OPENSTACK                          |   34 |
| R19  | Configurer le chiffrement TLSavec authentificationmutuellepour le servicedefiled'attente de messages          |   35 |
| R20  | Configurer le chiffrement TLS avec authentification mutuelle pour le service base de don- nées                |   35 |
| R21  | Mettre en place des tunnels IPsec entre le cache de jetons et les services OPENSTACK                          |   35 |
| R22  | Configurer le service glance pour qu'il s'appuis sur le service cinder                                        |   36 |
| R23  | Configurer le chiffrement TLS pour le service glance                                                          |   36 |
| R24  | Configurer le service barbican pour qu'il s'appuie sur un HSM)                                                |   37 |
| R25  | Utiliser un HSM ayant fait l'objet d'une certification de sécurité                                            |   37 |
| R26  | Utiliser le contrôle d'accès de barbican pour restreindre l'accès aux secrets                                 |   37 |
| R27  | Ne permettre l'accès au HSMque depuis les machines hébergeant le service barbican                             |   38 |
| R28  | Mettre en place des procédures pour automatiser le cycle de vie des secrets                                   |   38 |
| R29  | Mettre à disposition des commanditaires des procédures d'audit et de gestion des droits d'accès aux secrets   |   39 |
| R30  | Journaliser les accès aux secrets                                                                             |   39 |

### PyMuPDF (texte brut de la même zone)

```
R1
Configurer keystone pour utiliser un annuaire LDAP
16
R2
Utiliser plusieurs domaines et des annuaires LDAP dédiés par domaine
16
R3
Utiliser des ports TCP distincts pour les points d’entrée admin et public des services
19
R4
Placer les APIs public et admin sur des réseaux distincts
20
R5
Mettre en place un serveur mandataire inverse en amont des APIs à destination des com-
manditaires
20
R6
Mettre en place un filtrage applicatif en amont des APIs
22
R7
Mettre en place un mécanisme de de bloquage des jetons admin pour les APIs à destination
des commanditaires
23
R8
Mettre en place un mécanisme de de bloquage des jetons public pour les APIs à destination
du prestataire
24
R9
Mettre en place une authentification mutuelle entre le client OPENSTACK et le serveur man-
dataire
28
R10
Mettre en place un contrôle de cohérence entre le certificat X.509 et l’identité utilisateur
28
R11
Mémoriser les paires constituées du champ DN des certificats X.509 et des jetons émis par
le service keystone
29
R12
Vérifier les associations de jetons envoyés par les clients OPENSTACK et des certificats X.509
utilisés
29
R13
Activer le chiffrement des volumes du service nova
32
R14
Activer le chiffrement du stockage du service swift
32
R15
Activer le chiffrement des échanges entre les services swift et glance
32
R16
Activer le chiffrement des échanges entre les services glance et nova
32
R17
Protéger les clés de chiffrement
33
R18
Configurer le chiffrement TLS à l’état de l’art pour les APIs des services OPENSTACK
34
R19
Configurer le chiffrement TLS avec authentification mutuelle pour le service de file d’attente
de messages
35
R20
Configurer le chiffrement TLS avec authentification mutuelle pour le service base de don-
nées
35
R21
Mettre en place des tunnels IPsec entre le cache de jetons et les services OPENSTACK
35
R22
Configurer le service glance pour qu’il s’appuis sur le service cinder
36
R23
Configurer le chiffrement TLS pour le service glance
36
R24
Configurer le service barbican pour qu’il s’appuie sur un HSM)
37
R25
Utiliser un HSM ayant fait l’objet d’une certification de sécurité
37
R26
Utiliser le contrôle d’accès de barbican pour restreindre l’accès aux secrets
37
R27
Ne permettre l’accès au HSM que depuis les machines hébergeant le service barbican
38
R28
Mettre en place des procédures pour automatiser le cycle de vie des secrets
38
R29
Mettre à disposition des commanditaires des procédures d’audit et de gestion des droits
d’accès aux secrets
39
R30
Journaliser les accès aux secrets
39
```

## Tableau 5 — cartographie-si, page 40

### Docling

| Objet                  | Attribut                                                                                                                           |   Granularité | Objet pivot   |
|------------------------|------------------------------------------------------------------------------------------------------------------------------------|---------------|---------------|
| Commutateur (switch)   | Identification : identifiant et adresse IP                                                                                         |               |               |
| Commutateur (switch)   | Caractéristiques techniques : modèle, version du logiciel embarqué                                                                 |             1 |               |
| Commutateur (switch)   | Règles de filtrage des flux réseaux                                                                                                |               |               |
| Commutateur (switch)   | Équipement physique de support (si virtualisé)                                                                                     |             2 | Vue 6         |
| Routeur                | Identification : identifiant et adresse IP                                                                                         |               |               |
| Routeur                | Caractéristiques techniques : modèle, version du logiciel embarqué                                                                 |             1 |               |
| Routeur                | Règles de filtrage des flux réseaux                                                                                                |               |               |
| Routeur                | Équipement physique de support (si virtualisé)                                                                                     |             2 | Vue 6         |
| Équipement de sécurité | Identification (identifiant, adresse IP, adresse MAC) et description                                                               |               |               |
| Équipement de sécurité | Caractéristiques techniques : type d'équipement (sonde, pare-feu, SIEM, etc.), modèle, OS et version, version du logiciel embarqué |             1 |               |
| Équipement de sécurité | Équipement physique de support (si virtualisé)                                                                                     |               | Vue 6         |
| Serveur DHCP           | Identification (identifiant, adresse IP si fixe, adresse MAC) et                                                                   |             2 |               |
|                        | description                                                                                                                        |             2 |               |
|                        | Caractéristiques techniques : modèle, OS et version                                                                                |               |               |
|                        | Serveur physique de support (si machine virtuelle)                                                                                 |               | Vue 6         |
| Serveur DNS            | Identification (identifiant, adresse IP si fixe, adresse MAC) et description                                                       |               |               |
| Serveur DNS            | Caractéristiques techniques : modèle, OS et version                                                                                |             2 |               |
| Serveur DNS            | Serveur physique de support (si machine virtuelle)                                                                                 |               | Vue 6         |
| Serveur logique        | Identification (identifiant, adresse IP, adresse MAC) et description                                                               |               |               |
| Serveur logique        | Caractéristiques techniques : modèle, OS et version                                                                                |             1 |               |
| Serveur logique        | Services réseaux actifs                                                                                                            |               |               |
| Serveur logique        | Serveur physique de support                                                                                                        |             2 | Vue 6         |
| Serveur logique        | Applications liées                                                                                                                 |             1 | Vue 3         |

### PyMuPDF (texte brut de la même zone)

```
Objet
Attribut
Granularité
Objet pivot
Commutateur 
(switch)
Identification : identifiant et adresse IP
1
Caractéristiques techniques : modèle, version du logiciel 
embarqué
Règles de filtrage des flux réseaux
2
Équipement physique de support (si virtualisé)
Vue 6
Routeur
Identification : identifiant et adresse IP
1
Caractéristiques techniques : modèle, version du logiciel 
embarqué
Règles de filtrage des flux réseaux
2
Équipement physique de support (si virtualisé)
Vue 6
Équipement de 
sécurité
Identification (identifiant, adresse IP, adresse MAC) et 
description
1
Caractéristiques techniques : type d’équipement (sonde, 
pare-feu, SIEM, etc.), modèle, OS et version, version du logiciel 
embarqué
Équipement physique de support (si virtualisé)
2
Vue 6
Serveur DHCP
Identification (identifiant, adresse IP si fixe, adresse MAC) et 
description
2
Caractéristiques techniques : modèle, OS et version
Serveur physique de support (si machine virtuelle)
Vue 6
Serveur DNS
Identification (identifiant, adresse IP si fixe, adresse MAC) et 
description
2
Caractéristiques techniques : modèle, OS et version
Serveur physique de support (si machine virtuelle)
Vue 6
Serveur logique
Identification (identifiant, adresse IP, adresse MAC) et 
description
1
Caractéristiques techniques : modèle, OS et version
Services réseaux actifs
Serveur physique de support
2
Vue 6
Applications liées
1
Vue 3
```

## Tableau 6 — cartographie-si, page 3

### Docling

| Qu'est-ce qu'une cartographie ?                                                      |   5 |
|--------------------------------------------------------------------------------------|-----|
| Pourquoi réaliser une cartographie de son système d'information ?                    |   7 |
| Comment construire une cartographie du système d'information ?                       |   9 |
| Étape n°1 Comment initier la démarche de cartographie ?                              |  11 |
| 1 / Identifier les enjeux et parties prenantes de la construction de la cartographie |  12 |
| 2 / Définir le périmètre à cartographier                                             |  13 |
| 3 / Définir la cartographie cible et la trajectoire de construction                  |  14 |
| Étape n°2 Quel modèle dois-je adopter ?                                              |  15 |
| 1 / Collecter et analyser les éléments de cartographie existants                     |  16 |
| 2 / Définir le modèle de cartographie                                                |  17 |
| Étape n°3 Quels outils dois-je utiliser ?                                            |  18 |
| Étape n°4 Comment construire ma cartographie pas à pas ?                             |  21 |
| 1 / Réaliser l'inventaire du système d'information                                   |  22 |
| 2 / Construire les vues de la cartographie                                           |  23 |
| Étape n°5 Comment pérenniser ma cartographie ?                                       |  25 |
| 1 / Communiquer sur la cartographie                                                  |  26 |
| 2 / Maintenir la cartographie à jour                                                 |  27 |
| Facteurs clés de réussite                                                            |  29 |
| Annexe 1 Définition et proposition de contenu des différentes vues                   |  33 |
| 1 / Vue de l'écosystème                                                              |  34 |
| 2 / Vue métier du système d'information                                              |  34 |
| 3 / Vue des applications                                                             |  36 |
| 4 / Vue de l'administration                                                          |  38 |
| 5 / Vue des infrastructures logiques                                                 |  39 |
| 6 / Vue des infrastructures physiques                                                |  41 |
| Annexe 2 Proposition de cible et de trajectoire de construction de la cartographie   |  44 |
| Annexe 3 Exemple de cartographie                                                     |  46 |
| Annexe 4 Glossaire                                                                   |  52 |

### PyMuPDF (texte brut de la même zone)

```
Qu’est-ce qu’une cartographie ?
Pourquoi réaliser une cartographie de son système d’information ?
Comment construire une cartographie du système d’information ?
Étape n°1 Comment initier la démarche de cartographie ?
	
1 / Identifier les enjeux et parties prenantes de la construction de la cartographie
	
2 / Définir le périmètre à cartographier
	
3 / Définir la cartographie cible et la trajectoire de construction
Étape n°2 Quel modèle dois-je adopter ?
	
1 / Collecter et analyser les éléments de cartographie existants
	
2 / Définir le modèle de cartographie
Étape n°3 Quels outils dois-je utiliser ?
Étape n°4 Comment construire ma cartographie pas à pas ?
	
1 / Réaliser l’inventaire du système d’information
	
2 / Construire les vues de la cartographie
Étape n°5 Comment pérenniser ma cartographie ?
	
1 / Communiquer sur la cartographie
	
2 / Maintenir la cartographie à jour
Facteurs clés de réussite
Annexe 1 Définition et proposition de contenu des différentes vues
	
1 / Vue de l’écosystème
	
2 / Vue métier du système d’information
	
3 / Vue des applications
	
4 / Vue de l’administration
	
5 / Vue des infrastructures logiques
	
6 / Vue des infrastructures physiques
Annexe 2 Proposition de cible et de trajectoire de construction de la cartographie
Annexe 3 Exemple de cartographie
Annexe 4 Glossaire
5
7
9
11
12
13
14
15
16
17
18
21
22
23
25
26
27
29
33
34
34
36
38
39
41
44
46
52
```

## Tableau 7 — auth-mfa-mdp, page 13

### Docling

TABLE 1 - Récapitulatif des menaces et contre-mesures sur les mots de passe

| Menace                               | Contre-mesures                                                                                                                                                    |
|--------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Recherche exhaustive                 | Limite temporelle entre chaque essai (contre les attaquants en ligne) et fonctions de hachage ité- ratives dédiées (contre les attaquants en ligne et hors ligne) |
| Recherche par dictionnaire           | Mots de passe robustes et aléatoires et coffre- fort de mots de passe                                                                                             |
| Tables pré-calculées (rainbow table) | Sel aléatoire long                                                                                                                                                |
| Hameçonnage, ingénierie sociale      | Authentification multifacteur                                                                                                                                     |

### PyMuPDF (texte brut de la même zone)

```
Menace
Contre-mesures
Recherche exhaustive
Limite temporelle entre chaque essai (contre les
attaquants en ligne) et fonctions de hachage ité-
ratives dédiées (contre les attaquants en ligne et
hors ligne)
Recherche par dictionnaire
Mots de passe robustes et aléatoires et coffre-
fort de mots de passe
Tables pré-calculées (rainbow table)
Sel aléatoire long
Hameçonnage, ingénierie sociale
Authentification multifacteur
```

## Tableau 8 — admin-ad, page 151

### Docling

Tableau 5 - Liste des acronymes utilisés dans le document

| Acronyme   | Désignation                               |
|------------|-------------------------------------------|
| RBCD       | Ressource Based Constrained Delegation    |
| RDP        | Remote Desktop Protocol                   |
| RID        | Relative IDentifier                       |
| RODC       | Read Only Domain Controller               |
| RPC        | Remote Procedure Call                     |
| RSAT       | Remote System Administration Tools        |
| SAN        | Storage Area Network                      |
| SHA        | Secure Hash Algorithm                     |
| SI         | Système d'Information                     |
| SID        | Security IDentifier                       |
| SIIV       | Système d'Information d'Importance Vitale |
| SMB        | Simple Message Block                      |
| SPN        | Service Principal Name                    |
| SSI        | Sécurité des Systèmes d'Information       |
| TDO        | Trusted Domain Object                     |
| TGT        | Ticket Granting Ticket                    |
| TGS        | Ticket Granting Service                   |
| TLS        | Transport Layer Security                  |
| TPM        | Trusted Platform Module                   |
| UEFI       | Unified Extensible Firmware Interface     |
| UNC        | Universal Naming Conventio                |
| VLAN       | Virtual Local Area Network                |
| VM         | Virtual Machine                           |
| VPN        | Virtual Private Network                   |
| WBEM       | Web-Based Enterprise Management           |
| WDAC       | Windows Defender Application Control      |
| WDCG       | Windows Defender Credential Guard         |
| WDRCG      | Windows Defender Remote Credential Guard  |
| WINRM      | WINdows Remote Management                 |
| WSUS       | Windows Server Update Services            |
| XML        | eXtensible Markup Language                |

### PyMuPDF (texte brut de la même zone)

```
Acronyme
Désignation
RBCD
Ressource Based Constrained Delegation
RDP
Remote Desktop Protocol
RID
Relative IDentifier
RODC
Read Only Domain Controller
RPC
Remote Procedure Call
RSAT
Remote System Administration Tools
SAN
Storage Area Network
SHA
Secure Hash Algorithm
SI
Système d’Information
SID
Security IDentifier
SIIV
Système d’Information d’Importance Vitale
SMB
Simple Message Block
SPN
Service Principal Name
SSI
Sécurité des Systèmes d’Information
TDO
Trusted Domain Object
TGT
Ticket Granting Ticket
TGS
Ticket Granting Service
TLS
Transport Layer Security
TPM
Trusted Platform Module
UEFI
Unified Extensible Firmware Interface
UNC
Universal Naming Conventio
VLAN
Virtual Local Area Network
VM
Virtual Machine
VPN
Virtual Private Network
WBEM
Web-Based Enterprise Management
WDAC
Windows Defender Application Control
WDCG
Windows Defender Credential Guard
WDRCG
Windows Defender Remote Credential Guard
WINRM
WINdows Remote Management
WSUS
Windows Server Update Services
XML
eXtensible Markup Language
```

## Tableau 9 — openstack, page 73

### Docling

| Champ            | Valeur                                           | Explication                                                                                                                                  |
|------------------|--------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| target.addresses | Plusieurs URLs avec des noms associés différents | Chacune de ces URLs correspond à l'end- point de destination de la requête en fonc- tion du niveau d'accès requis (admin, pri- vate, public) |
| requestPath      | /v2.1/servers /detail                            | Endpoint de l'API destinataire. Ici, cela signi- fie que la requête demande la liste des dé- tails pour chacun des serveurs.                 |
| reasonCode       | 200                                              | Corresponds au code HTTP de retour de l'API. Ici, la valeur 200 nous confirme que la requête a bien été traitée.                             |

### PyMuPDF (texte brut de la même zone)

```
Champ
Valeur
Explication
target.addresses Plusieurs URLs avec des
noms associés différents
Chacune de ces URLs correspond à l’end-
point de destination de la requête en fonc-
tion du niveau d’accès requis (admin, pri-
vate, public)
requestPath
/v2.1/servers /detail
Endpoint de l’API destinataire. Ici, cela signi-
fie que la requête demande la liste des dé-
tails pour chacun des serveurs.
reasonCode
200
Corresponds au code HTTP de retour de
l’API. Ici, la valeur 200 nous confirme que la
requête a bien été traitée.
```

## Tableau 10 — admin-ad, page 15

### Docling

Tableau 1 - Description des Tiers dans le modèle en trois Tiers de Microsoft

|   Tier | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
|--------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|      0 | Ce Tier représente le cœur de confiance de l'organisation. Les privilèges d'administration de ce Tier sont les plus élevés : ils permettent l'octroi de privilèges sur les autres Tiers et donc le contrôle de toutes les ressources de l'annuaire AD. Les ressources de ce Tier - telles que les contrôleurs de domaine AD par exemple - ont de facto un niveau de sensibilité équivalent dans la mesure où la détention de privilèges d'administration sur l'une d'elles induit l'acquisition des privilèges d'administration sur les autres. La compromission d'une ressource de ce Tier, au delà de permettre la compromission de l'ensemble des ressources de l'AD, permet aussi l'aménagement de portes dérobées potentiellement complexes à identifier et à éradiquer. Une telle compromission nécessi- terait une remédiation extrêmement longue, compliquée et couteuse à mettre en œuvre pour rétablir la confiance dans le SI.                                                                                                                                                                                                                                                                                                                             |
|      1 | Ce Tier représente la confiance dans les données et plus précisément, au sens de la méthode EBIOS RM [10], la confiance dans les valeurs métiers de l'organisation. Il représente ainsi la confiance dans les biens métiers ainsi que dans les biens supports qui les portent (stockage, traitement, etc.). Ces derniers peuvent par exemple être des serveurs de gestion de code source pour une entreprise de développement logiciel, ou bien les équipements critiques d'une chaîne de production pour un industriel. Les privilèges d'administration afférents à ce Tier permettent le contrôle de tout ou d'un ensemble de ces biens supports et sont généralement octroyés à des administrateurs sys- tème ou à des responsables d'applications ou de services du SI.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
|      2 | Ce Tier représente la confiance dans les postes de travail des utilisateurs du SI et plus largement dans tout moyens d'accès à la donnée métier. Les ressources du Tier 2 sont généralement des postes de travail de bureautique, mais peuvent également être des consoles industrielles ou tout autre type de moyen d'accès utilisateur ou de programmation. Les privilèges d'administration afférents à ce Tier permettent le contrôle de tout ou d'un ensemble de ces moyens d'accès. Un tel niveau de droits et privilèges est généralement accordé à des téléadministrateurs des postes bureautiques, des administrateurs de services de déploiement des postes bureautiques, des déployeurs de consoles industrielles, etc. Ces moyens d'accès hébergent des portions de valeurs métiers de l'organisation ou per- mettent d'y accéder. La compromission d'un ensemble de moyens d'accès peut ainsi per- mettre un large accès aux données de l'organisation ou à ses valeurs métiers, depuis le SI interne ou même parfois depuis Internet. Il arrive par ailleurs que des utilisateurs haut placés dans la hiérarchie de l'organisation aient des droits d'accès très larges sur les valeurs métiers, ce qui en fait des cibles de choix pour des attaquants. |

### PyMuPDF (texte brut de la même zone)

```
Tier
Description
0
Ce Tier représente le cœur de confiance de l’organisation.
Les privilèges d’administration de ce Tier sont les plus élevés : ils permettent l’octroi de
privilèges sur les autres Tiers et donc le contrôle de toutes les ressources de l’annuaire AD.
Les ressources de ce Tier – telles que les contrôleurs de domaine AD par exemple – ont
de facto un niveau de sensibilité équivalent dans la mesure où la détention de privilèges
d’administration sur l’une d’elles induit l’acquisition des privilèges d’administration sur
les autres.
La compromission d’une ressource de ce Tier, au delà de permettre la compromission
de l’ensemble des ressources de l’AD, permet aussi l’aménagement de portes dérobées
potentiellement complexes à identifier et à éradiquer. Une telle compromission nécessi-
terait une remédiation extrêmement longue, compliquée et couteuse à mettre en œuvre
pour rétablir la confiance dans le SI.
1
Ce Tier représente la confiance dans les données et plus précisément, au sens de la
méthode EBIOS RM [10], la confiance dans les valeurs métiers de l’organisation.
Il représente ainsi la confiance dans les biens métiers ainsi que dans les biens supports
qui les portent (stockage, traitement, etc.). Ces derniers peuvent par exemple être des
serveurs de gestion de code source pour une entreprise de développement logiciel, ou
bien les équipements critiques d’une chaîne de production pour un industriel.
Les privilèges d’administration afférents à ce Tier permettent le contrôle de tout ou d’un
ensemble de ces biens supports et sont généralement octroyés à des administrateurs sys-
tème ou à des responsables d’applications ou de services du SI.
2
Ce Tier représente la confiance dans les postes de travail des utilisateurs du SI et plus
largement dans tout moyens d’accès à la donnée métier.
Les ressources du Tier 2 sont généralement des postes de travail de bureautique, mais
peuvent également être des consoles industrielles ou tout autre type de moyen d’accès
utilisateur ou de programmation. Les privilèges d’administration afférents à ce Tier
permettent le contrôle de tout ou d’un ensemble de ces moyens d’accès. Un tel niveau
de droits et privilèges est généralement accordé à des téléadministrateurs des postes
bureautiques, des administrateurs de services de déploiement des postes bureautiques,
des déployeurs de consoles industrielles, etc.
Ces moyens d’accès hébergent des portions de valeurs métiers de l’organisation ou per-
mettent d’y accéder. La compromission d’un ensemble de moyens d’accès peut ainsi per-
mettre un large accès aux données de l’organisation ou à ses valeurs métiers, depuis le SI
interne ou même parfois depuis Internet. Il arrive par ailleurs que des utilisateurs haut
placés dans la hiérarchie de l’organisation aient des droits d’accès très larges sur les valeurs
métiers, ce qui en fait des cibles de choix pour des attaquants.
```

## Tableau 11 — openssh, page 2

### Docling

|   Version | Date            | Nature des modifications     |
|-----------|-----------------|------------------------------|
|       1.0 | 6 avril 2013    | Version initiale             |
|       1.1 | 15 avril 2013   | Corrections de forme         |
|       1.2 | 21 janvier 2014 | Compléments                  |
|       1.3 | 17 août 2015    | Mise à jour charte graphique |

### PyMuPDF (texte brut de la même zone)

```
Version
Date
Nature des modiﬁcations
1.0
6 avril 2013
Version initiale
1.1
15 avril 2013
Corrections de forme
1.2
21 janvier 2014
Compléments
1.3
17 août 2015
Mise à jour charte graphique
```

## Tableau 12 — tls, page 51

### Docling

Table A.1 - Suites recommandées définies pour TLS 1.3

| Code TLS   | Suite cryptographique        |
|------------|------------------------------|
| 0x1302     | TLS_AES_256_GCM_SHA384       |
| 0x1301     | TLS_AES_128_GCM_SHA256       |
| 0x1304     | TLS_AES_128_CCM_SHA256       |
| 0x1303     | TLS_CHACHA20_POLY1305_SHA256 |

### PyMuPDF (texte brut de la même zone)

```
Code TLS
Suite cryptographique
0x1302
TLS_AES_256_GCM_SHA384
0x1301
TLS_AES_128_GCM_SHA256
0x1304
TLS_AES_128_CCM_SHA256
0x1303
TLS_CHACHA20_POLY1305_SHA256
```

## Tableau 13 — journalisation-ad, page 77

### Docling

| Paramètres         | Valeurs                                                                                                                                                                                                                                                                                                                                                                                                                     |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| LogFile            | Le nom du journal de destination sur le serveur collecteur (le journal « Évènements transférés » ou tout autre journal personnalisé).                                                                                                                                                                                                                                                                                       |
| MaxItems           | Une vague de transfert est déclenchée lorsque ce nombre maximum d'évènements en attente de transfert au serveur collecteur est atteint. Si la valeur est de 1, une vague de transfert est déclenchée dès qu'un évènement est journalisé, ce qui risque de générer de nombreuses con- nexions réseau vers le serveur collecteur. Il n'est généralement pas né- cessaire de changer la valeur par défaut (50 000 évènements). |
| MaxLatencyTime     | Temps maximum d'attente entre chaque vague de transfert d' évène- ments au serveur collecteur, exprimé en millisecondes. La valeur par défaut de 15 minutes (900 000 millisecondes) est généralement un bon compromis.                                                                                                                                                                                                      |
| ReadExistingEvents | La valeur false indique au client de seulement transférer les futurs évè- nements, tandis que la valeur true indique de transférer tous les évène- ments passés a et futurs.                                                                                                                                                                                                                                                |
| SubscriptionType   | Le type d'abonnement doit correspondre au Deliverymode configuré : - SourceInitiated pour le <Delivery Mode="Push">; - CollectorInitiated pour le mode <Delivery Mode="Pull">.                                                                                                                                                                                                                                              |

### PyMuPDF (texte brut de la même zone)

```
Paramètres
Valeurs
LogFile
Le nom du journal de destination sur le serveur collecteur (le journal
« Évènements transférés » ou tout autre journal personnalisé).
MaxItems
Une vague de transfert est déclenchée lorsque ce nombre maximum
d’évènements en attente de transfert au serveur collecteur est atteint.
Si la valeur est de 1, une vague de transfert est déclenchée dès qu’un
évènement est journalisé, ce qui risque de générer de nombreuses con-
nexions réseau vers le serveur collecteur. Il n’est généralement pas né-
cessaire de changer la valeur par défaut (50 000 évènements).
MaxLatencyTime
Temps maximum d’attente entre chaque vague de transfert d’ évène-
ments au serveur collecteur, exprimé en millisecondes. La valeur par
défaut de 15 minutes (900 000 millisecondes) est généralement un bon
compromis.
ReadExistingEvents
La valeur false indique au client de seulement transférer les futurs évè-
nements, tandis que la valeur true indique de transférer tous les évène-
ments passésa et futurs.
SubscriptionType
Le type d’abonnement doit correspondre au Deliverymode configuré :
- SourceInitiated pour le <Delivery Mode="Push">;
- CollectorInitiated pour le mode <Delivery Mode="Pull">.
```

## Tableau 14 — active-directory, page 47

### Docling

Table 12 - Droits et privilèges

| Nom                             | Description                                                                                                                        |
|---------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| SeRestorePrivilege              | Restaurer les fichiers et les répertoires                                                                                          |
| SeSecurityPrivilege             | Gérer le journal d'audit et de sécurité                                                                                            |
| SeShutdownPrivilege             | Éteindre la machine                                                                                                                |
| SeSyncAgentPrivilege            | Lire tous les objets et du domaine AD et leurs propriétés                                                                          |
| SeSystemEnvironmentPrivilege    | Modifier des variables d'environnement dans les NVRAM                                                                              |
| SeSystemProfilePrivilege        | Récolter des données relatives à la performance du système en général                                                              |
| SeSystemtimePrivilege           | Changer l'heure du système                                                                                                         |
| SeTakeOwnershipPrivilege        | Prendre possession de fichiers ou d'autres objets                                                                                  |
| SeTcbPrivilege                  | Agir en tant que partie du système d'exploitation                                                                                  |
| SeTimeZonePrivilege             | Changer le fuseau horaire du système                                                                                               |
| SeTrustedCredManAccessPrivilege | Accès avancé au sous-système de gestion des crédences. Par défauts seuls les processus WinLogon et LSASS disposent de ce privilège |
| SeUndockPrivilege               | Retirer de manière logicielle un portable de sa station d'ac- cueil                                                                |

### PyMuPDF (texte brut de la même zone)

```
Nom
Description
SeRestorePrivilege
Restaurer les ﬁchiers et les répertoires
SeSecurityPrivilege
Gérer le journal d’audit et de sécurité
SeShutdownPrivilege
Éteindre la machine
SeSyncAgentPrivilege
Lire tous les objets et du domaine AD et leurs propriétés
SeSystemEnvironmentPrivilege
Modiﬁer des variables d’environnement dans les NVRAM
SeSystemProﬁlePrivilege
Récolter des données relatives à la performance du système
en général
SeSystemtimePrivilege
Changer l’heure du système
SeTakeOwnershipPrivilege
Prendre possession de ﬁchiers ou d’autres objets
SeTcbPrivilege
Agir en tant que partie du système d’exploitation
SeTimeZonePrivilege
Changer le fuseau horaire du système
SeTrustedCredManAccessPrivilege
Accès avancé au sous-système de gestion des crédences. Par
défauts seuls les processus WinLogon et LSASS disposent de
ce privilège
SeUndockPrivilege
Retirer de manière logicielle un portable de sa station d’ac-
cueil
```

## Tableau 15 — mecanismes-crypto, page 51

### Docling

Table 2 - Ordre de grandeur de la valeur de 2k pour le calcul

|   2 k | Ordre de grandeur                                                                                |
|-------|--------------------------------------------------------------------------------------------------|
|   215 | Opérations élémentaires nécessaires pour l'implémentation d'une primitive symétrique.            |
|   232 | Opérations par seconde par cœur de processeur 4 GHz.                                             |
|   246 | Opérations effectuables par seconde sur processeur graphique (GPU).                              |
|   257 | Opérations par an par cœur de processeur.                                                        |
|   260 | Opérations par seconde effectuables par les meilleurs supercalculateurs connus.                  |
|   270 | Empreintes SHA-256 calculées chaque seconde dans le monde pour pour la blockchain Bitcoin.       |
|   271 | Opérations effectuables par an sur GPU.                                                          |
|   276 | Opérations par jour effectuables par les meilleurs supercalculateurs connus.                     |
|   291 | Opérations effectuables en un siècle par les meilleurs supercalculateurs connus.                 |
|   296 | Empreintes SHA-256 calculées pour la blockchain Bitcoin entre sa création en 2009 et 2025.       |
|  2119 | Opérations effectuables en 13.8 milliards d'années par les meilleurs supercal- culateurs connus. |
|  2128 | Opérations effectuables en 13.8milliards d'années par l'ensemble des proces- seurs mondiaux.     |
|  2256 | Électrons dans l'univers.                                                                        |

### PyMuPDF (texte brut de la même zone)

```
2k
Ordre de grandeur
215
Opérations élémentaires nécessaires pour l’implémentation d’une primitive
symétrique.
232
Opérations par seconde par cœur de processeur 4 GHz.
246
Opérations effectuables par seconde sur processeur graphique (GPU).
257
Opérations par an par cœur de processeur.
260
Opérations par seconde effectuables par les meilleurs supercalculateurs
connus.
270
Empreintes SHA-256 calculées chaque seconde dans le monde pour pour la
blockchain Bitcoin.
271
Opérations effectuables par an sur GPU.
276
Opérations par jour effectuables par les meilleurs supercalculateurs connus.
291
Opérations effectuables en un siècle par les meilleurs supercalculateurs
connus.
296
Empreintes SHA-256 calculées pour la blockchain Bitcoin entre sa création en
2009 et 2025.
2119
Opérations effectuables en 13.8 milliards d’années par les meilleurs supercal-
culateurs connus.
2128
Opérations effectuables en 13.8 milliards d’années par l’ensemble des proces-
seurs mondiaux.
2256
Électrons dans l’univers.
```

## Tableau 16 — guide-conteneurs, page 18

### Docling

| Recommandations   | CIS Docker Community Edition Benchmark v1.1.0   | CIS Docker Community Edition Benchmark v1.1.0                                                                                                 |
|-------------------|-------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| R16               | 2.12                                            | Ensure centralized and remote logging is configured                                                                                           |
| R1                | 5.4 5.31                                        | Ensure privileged containers are not used Ensure the Docker socket is not mounted inside any containers                                       |
| R2                | 5.17                                            | Ensure host devices are not directly exposed to containers                                                                                    |
| R3                | 5.29                                            | Ensure Docker's default bridge docker0 is not used                                                                                            |
| R4                | 5.9                                             | Ensure the host's network namespace is not shared                                                                                             |
| R6                | 5.15 5.16 5.20                                  | Ensure the host's process namespace is not shared Ensure the host's IPC namespace is not shared Ensure the host's UTS namespace is not shared |
| R7                | 2.8 5.30                                        | Enable user namespace support Ensure the host's user namespaces is not shared                                                                 |
| R8                | 5.3                                             | Ensure Linux Kernel Capabilities are restricted within containers                                                                             |
| R9                | 5.24                                            | Ensure cgroup usage is confirmed                                                                                                              |
| R10               | 5.10                                            | Ensure memory usage for container is limited                                                                                                  |
| R12               | 5.12                                            | Ensure the container's root filesystem is mounted as read only                                                                                |
| R15               | 5.5                                             | Ensure sensitive host system directories are not mounted on containers                                                                        |

### PyMuPDF (texte brut de la même zone)

```
Recommandations
CIS Docker Community Edition Benchmark v1.1.0
R16
2.12 Ensure centralized and remote logging is conﬁgured
R1
5.4
Ensure privileged containers are not used
5.31 Ensure the Docker socket is not mounted inside any containers
R2
5.17 Ensure host devices are not directly exposed to containers
R3
5.29 Ensure Docker’s default bridge docker0 is not used
R4
5.9
Ensure the host’s network namespace is not shared
R6
5.15 Ensure the host’s process namespace is not shared
5.16 Ensure the host’s IPC namespace is not shared
5.20 Ensure the host’s UTS namespace is not shared
R7
2.8
Enable user namespace support
5.30 Ensure the host’s user namespaces is not shared
R8
5.3
Ensure Linux Kernel Capabilities are restricted within containers
R9
5.24 Ensure cgroup usage is conﬁrmed
R10
5.10 Ensure memory usage for container is limited
R12
5.12 Ensure the container’s root ﬁlesystem is mounted as read only
R15
5.5
Ensure sensitive host system directories are not mounted on containers
```

## Tableau 17 — active-directory, page 4

### Docling

|         | 3.5.1                                                     | Périmètre des groupes .                                                      | . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25   |
|---------|-----------------------------------------------------------|------------------------------------------------------------------------------|--------------------------------------------------------------------|
|         | 3.5.2                                                     | Utilisation des groupes de Domaine local                                     | . . . . . . . . . . . . . . . . . . . . . . 25                     |
|         | 3.5.3                                                     | Utilisation des groupes Globaux . .                                          | . . . . . . . . . . . . . . . . . . . . . . . . . 25               |
|         | 3.5.4                                                     | Utilisation des groupes Universels .                                         | . . . . . . . . . . . . . . . . . . . . . . . . . 25               |
|         | 3.5.5                                                     | Modification de l'étendue de groupe                                          | . . . . . . . . . . . . . . . . . . . . . . . . 25                 |
|         | 3.5.6                                                     | Bouclage . . . . . . . . . . . . . . .                                       | . . . . . . . . . . . . . . . . . . . . . . . . . 26               |
|         | 3.5.7                                                     | Contrôle d'accès basé sur des rôles                                          | . . . . . . . . . . . . . . . . . . . . . . . . . 26               |
|         | 3.5.8                                                     | Taille du ticket Kerberos . . . . . .                                        | . . . . . . . . . . . . . . . . . . . . . . . . . 26               |
|         | 3.5.9                                                     | Règles de nommage . . . . . . . .                                            | . . . . . . . . . . . . . . . . . . . . . . . . . 27               |
| 3.6     | Gestion des comptes . . .                                 | . . . . . . . . .                                                            | . . . . . . . . . . . . . . . . . . . . . . . . . 27               |
|         | 3.6.1                                                     | Stockage des secrets d'authentification                                      | . . . . . . . . . . . . . . . . . . . . . . . 28                   |
|         | 3.6.2                                                     | Authentification . . . . . . . . . .                                         | . . . . . . . . . . . . . . . . . . . . . . . . . 29               |
|         |                                                           | 3.6.2.1 Protocoles . . . . . . . . . 3.6.2.2 Authentification multi-facteurs | . . . . . . . . . . . . . . . . . . . . . . . . 29                 |
|         | 3.6.3                                                     | . . . . . . .                                                                | . . . . . . . . . . . . . . . . . . . . . . 30                     |
|         |                                                           | Catégorisation des comptes                                                   | . . . . . . . . . . . . . . . . . . . . . . 30                     |
|         |                                                           | 3.6.3.1 Comptes privilégiés . . .                                            | . . . . . . . . . . . . . . . . . . . . . . . . . 32               |
|         | 3.6.4                                                     | Règles de nommage . . . . . . . .                                            | . . . . . . . . . . . . . . . . . . . . . . . . . 32               |
|         | 3.6.5                                                     | Scripts . . . . . . . . . . . . . . . .                                      | . . . . . . . . . . . . . . . . . . . . . . . . . 33               |
|         | 3.6.6                                                     | Sécurité des comptes . . . . . . . .                                         | . . . . . . . . . . . . . . . . . . . . . . . . . 33               |
|         |                                                           | 3.6.6.1 Mots de passe . . . . . .                                            | . . . . . . . . . . . . . . . . . . . . . . . . . 33               |
|         |                                                           | 3.6.6.2 Comptes inactifs . . . . .                                           | . . . . . . . . . . . . . . . . . . . . . . . . . 34               |
| 4       | Mesures organisationnelles préventives                    | Mesures organisationnelles préventives                                       | 34                                                                 |
| 4.1     | Gestion des ressources humaines                           | . . . . .                                                                    | . . . . . . . . . . . . . . . . . . . . . . . . . 34               |
| 4.2     | Intégrer la gestion des comptes dans les processus métier | Intégrer la gestion des comptes dans les processus métier                    | . . . . . . . . . . . . . . . . . 35                               |
| 4.3     | Audits et amélioration continue .                         | . . . . .                                                                    | . . . . . . . . . . . . . . . . . . . . . . . . . 35               |
| Annexes | Annexes                                                   | Annexes                                                                      | 38                                                                 |

### PyMuPDF (texte brut de la même zone)

```
3.5.1
Périmètre des groupes . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
25
3.5.2
Utilisation des groupes de Domaine local . . . . . . . . . . . . . . . . . . . . . .
25
3.5.3
Utilisation des groupes Globaux . . . . . . . . . . . . . . . . . . . . . . . . . . .
25
3.5.4
Utilisation des groupes Universels . . . . . . . . . . . . . . . . . . . . . . . . . .
25
3.5.5
Modiﬁcation de l’étendue de groupe
. . . . . . . . . . . . . . . . . . . . . . . .
25
3.5.6
Bouclage . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
26
3.5.7
Contrôle d’accès basé sur des rôles . . . . . . . . . . . . . . . . . . . . . . . . .
26
3.5.8
Taille du ticket Kerberos . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
26
3.5.9
Règles de nommage
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
27
3.6
Gestion des comptes . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
27
3.6.1
Stockage des secrets d’authentiﬁcation . . . . . . . . . . . . . . . . . . . . . . .
28
3.6.2
Authentiﬁcation
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
29
3.6.2.1
Protocoles
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
29
3.6.2.2
Authentiﬁcation multi-facteurs . . . . . . . . . . . . . . . . . . . . . .
30
3.6.3
Catégorisation des comptes
. . . . . . . . . . . . . . . . . . . . . . . . . . . . .
30
3.6.3.1
Comptes privilégiés
. . . . . . . . . . . . . . . . . . . . . . . . . . . .
32
3.6.4
Règles de nommage
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
32
3.6.5
Scripts . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
33
3.6.6
Sécurité des comptes . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
33
3.6.6.1
Mots de passe
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
33
3.6.6.2
Comptes inactifs . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
34
4
Mesures organisationnelles préventives
34
4.1
Gestion des ressources humaines
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
34
4.2
Intégrer la gestion des comptes dans les processus métier . . . . . . . . . . . . . . . . .
35
4.3
Audits et amélioration continue . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
35
Annexes
38
```

## Tableau 18 — active-directory, page 3

### Docling

|   1 Introduction | 1 Introduction                                                               | 1 Introduction                                                                 | 1 Introduction                                                               | 4                     |
|------------------|------------------------------------------------------------------------------|--------------------------------------------------------------------------------|------------------------------------------------------------------------------|-----------------------|
|              1.1 | Quels risques de sécurité ? . . . . . . . . . . . . . . . . . . . . . . .    | Quels risques de sécurité ? . . . . . . . . . . . . . . . . . . . . . . .      | . . .                                                                        | . . . . . . . . 4     |
|              1.2 | Objectifs et périmètre du document . . . . . . . . . . . . . . . . . .       | Objectifs et périmètre du document . . . . . . . . . . . . . . . . . .         | . . .                                                                        | . . . . . . . . 4     |
|              1.3 | Priorisation des recommandations . . . . . . . . . . . . . . . . . . . . . . | Priorisation des recommandations . . . . . . . . . . . . . . . . . . . . . .   | Priorisation des recommandations . . . . . . . . . . . . . . . . . . . . . . | . . . . . . . . 4     |
|              1.4 | Concepts . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .       | Concepts . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .         | . . . . .                                                                    | . . . . . . . . 5     |
|                  | 1.4.1                                                                        | Annuaire Active Directory . .                                                  | . . . . . . . .                                                              | . . . . . . . . 5     |
|                  | 1.4.2                                                                        | . . . . . . . . . . . . Forêt et domaine . . . . . . . . . . . . . . . . . . . | . . . . . . . .                                                              | . . . . . . . . 6     |
|                2 | Prérequis à la sécurisation de l'Active Directory                            | Prérequis à la sécurisation de l'Active Directory                              | Prérequis à la sécurisation de l'Active Directory                            | 6                     |
|              2.1 | Architecture physique . . . . . . . . . . . . . . .                          | Architecture physique . . . . . . . . . . . . . . .                            | . . . . . . . . . . . . .                                                    | . . . . . . . . 6     |
|                  | 2.1.1                                                                        | Sites Active Directory . . . . . . . .                                         | . . . . . . . . . . . . . . . .                                              | . . . . . . . . 7     |
|                  | 2.1.2                                                                        | La réplication . . . . . . . . . . . . . . . . . . . . . . . .                 | . . . . .                                                                    | . . . . . . . . 7     |
|                  |                                                                              | 2.1.2.1                                                                        | Port utilisé par la réplication . . . . . . . . . . . . . . .                | . . . . . . . . 8     |
|                  |                                                                              | 2.1.2.2                                                                        | Utilisation du KCC . . . . . . . . . . . . . . . . . . . .                   | . . . . . . . . 8     |
|                  |                                                                              | 2.1.2.3                                                                        | Planification et fréquence de la réplication . . . . . . . .                 | . . . . . . . . 9     |
|                  | 2.1.3                                                                        | Placement des contrôleurs de domaine . . . . . .                               | . . . . . . . . .                                                            | . . . . . . . . 9     |
|              2.2 | Architecture réseau . . . . . . . . . . . . . . . . . . . . . . . .          | Architecture réseau . . . . . . . . . . . . . . . . . . . . . . . .            | . . . . . .                                                                  | . . . . . . . . 10    |
|                  | 2.2.1                                                                        | DNS . . . . . . . . . . . . . . . . . . . . . . . .                            | DNS . . . . . . . . . . . . . . . . . . . . . . . .                          | . . . . . . . . 10    |
|                  |                                                                              | 2.2.1.1                                                                        | . . . . . . . . . . Rappel sur la méthode de résolution des noms d'hôtes .   | . . . . . . . . 11    |
|                  |                                                                              | 2.2.1.2                                                                        | Rappel sur les zones de recherche . . . . . . . . . . . . .                  | . . . . . . . . 11    |
|                  |                                                                              | 2.2.1.3                                                                        | Rappel sur les types de zones . . . . . . . . . . . . . . .                  | . . . . . . . . 11    |
|              2.3 | Santé des                                                                    | contrôleurs de domaine . . .                                                   | . . . . . . . . . . . . . . . . . . .                                        | . . . . . . . . 12    |
|                  | 2.3.1 Journalisation . . . . . . . . . . . .                                 | 2.3.1 Journalisation . . . . . . . . . . . .                                   | . . . . . . . . . . . . . . . . .                                            | . . . . . . . . 12    |
|              2.4 | Accès à distance . . . . . . . . . . . . . . . . . . . . . . . . . . .       | Accès à distance . . . . . . . . . . . . . . . . . . . . . . . . . . .         | . . . .                                                                      | . . . . . . . . 14    |
|              2.5 | Environnement logiciel . . . . . . . . . . . . .                             | Environnement logiciel . . . . . . . . . . . . .                               | . . . . . . . . . . . . . . .                                                | . . . . . . . . 14    |
|                3 | Éléments de sécurité Active Directory                                        | Éléments de sécurité Active Directory                                          | Éléments de sécurité Active Directory                                        | 15                    |
|              3.1 | Niveaux fonctionnels . . . . . . . . . . . .                                 | Niveaux fonctionnels . . . . . . . . . . . .                                   | . . . . . . . . . . . . . . . . .                                            | . . . . . . . . 15    |
|              3.2 | Schéma . . . . . . . . . . . . . . . . . . . . . . . . . . .                 | Schéma . . . . . . . . . . . . . . . . . . . . . . . . . . .                   | . . . . . . . . .                                                            | . . . . . . . . 16    |
|              3.3 | Architecture logique . . . . . . . . . . . . . . . . . . . . . . . . . . .   | Architecture logique . . . . . . . . . . . . . . . . . . . . . . . . . . .     | . .                                                                          | . . . . . . . . 17    |
|                  | 3.3.1                                                                        | Relations d'approbation . . .                                                  | . . . . . . . . . . . . . . . . . . . .                                      | . . . . . . . . 17    |
|                  |                                                                              | 3.3.1.1                                                                        | Types des relations d'approbation . . . . . . . . . . . .                    | . . . . . . . . 17    |
|                  |                                                                              | 3.3.1.2                                                                        | Transitivité des relations d'approbation . . . . . . . . .                   | . . . . . . . . 18    |
|                  |                                                                              | 3.3.1.3                                                                        | Direction des relations d'approbation . . . . . . . . . .                    | . . . . . . . . 18    |
|                  |                                                                              | 3.3.1.4                                                                        | Étendue de l'authentification des utilisateurs . . . . . .                   | . . . . . . . . 18    |
|                  |                                                                              | 3.3.1.5                                                                        | Historique des SIDs . . . . . . . . . . . . . . . . . . . .                  | . . . . . . . . 19    |
|                  |                                                                              | 3.3.1.6                                                                        | Filtrage des SIDs . . . . . . . . . . . . . . . . . . . . . .                | . . . . . . . . 19    |
|                  | 3.3.2                                                                        | Les unités organisationnelles . . . . . . . . .                                | . . . . . . . . . . . .                                                      | . . . . . . . . 19    |
|                  | 3.3.3 Rôles de maître d'opérations . . . .                                   | 3.3.3 Rôles de maître d'opérations . . . .                                     | . . . . . . . . . . . . . . . .                                              | . . . . . . . . 20    |
|              3.4 | Les stratégies de groupe . . . . . . . . . . . . . . . . .                   | Les stratégies de groupe . . . . . . . . . . . . . . . . .                     | . . . . . . . . . .                                                          | . . . . . . . . 21    |
|                  | 3.4.1 Règles de nommage . . . . . . . .                                      | 3.4.1 Règles de nommage . . . . . . . .                                        | . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      | 23 . . . . . . . . 23 |
|              3.5 | 3.4.2 Règles d'implémentation . . . . de sécurité . . . . . . . . . . .      | 3.4.2 Règles d'implémentation . . . . de sécurité . . . . . . . . . . .        | . . . . . . . . . . . . . . . . . . .                                        | . . . . . . . . 23    |
|                  | Groupes                                                                      | Groupes                                                                        | Groupes                                                                      |                       |

### PyMuPDF (texte brut de la même zone)

```
1
Introduction
4
1.1
Quels risques de sécurité ? . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4
1.2
Objectifs et périmètre du document . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4
1.3
Priorisation des recommandations . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
4
1.4
Concepts . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
5
1.4.1
Annuaire Active Directory . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
5
1.4.2
Forêt et domaine . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
6
2
Prérequis à la sécurisation de l’Active Directory
6
2.1
Architecture physique
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
6
2.1.1
Sites Active Directory . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
7
2.1.2
La réplication . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
7
2.1.2.1
Port utilisé par la réplication . . . . . . . . . . . . . . . . . . . . . . .
8
2.1.2.2
Utilisation du KCC
. . . . . . . . . . . . . . . . . . . . . . . . . . . .
8
2.1.2.3
Planiﬁcation et fréquence de la réplication . . . . . . . . . . . . . . . .
9
2.1.3
Placement des contrôleurs de domaine . . . . . . . . . . . . . . . . . . . . . . .
9
2.2
Architecture réseau . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
10
2.2.1
DNS . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
10
2.2.1.1
Rappel sur la méthode de résolution des noms d’hôtes . . . . . . . . .
11
2.2.1.2
Rappel sur les zones de recherche . . . . . . . . . . . . . . . . . . . . .
11
2.2.1.3
Rappel sur les types de zones . . . . . . . . . . . . . . . . . . . . . . .
11
2.3
Santé des contrôleurs de domaine . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
12
2.3.1
Journalisation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
12
2.4
Accès à distance
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
14
2.5
Environnement logiciel . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
14
3
Éléments de sécurité Active Directory
15
3.1
Niveaux fonctionnels . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
15
3.2
Schéma
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
16
3.3
Architecture logique
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
17
3.3.1
Relations d’approbation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
17
3.3.1.1
Types des relations d’approbation
. . . . . . . . . . . . . . . . . . . .
17
3.3.1.2
Transitivité des relations d’approbation . . . . . . . . . . . . . . . . .
18
3.3.1.3
Direction des relations d’approbation
. . . . . . . . . . . . . . . . . .
18
3.3.1.4
Étendue de l’authentiﬁcation des utilisateurs . . . . . . . . . . . . . .
18
3.3.1.5
Historique des SIDs
. . . . . . . . . . . . . . . . . . . . . . . . . . . .
19
3.3.1.6
Filtrage des SIDs . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
19
3.3.2
Les unités organisationnelles . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
19
3.3.3
Rôles de maître d’opérations
. . . . . . . . . . . . . . . . . . . . . . . . . . . .
20
3.4
Les stratégies de groupe . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
21
3.4.1
Règles de nommage
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
23
3.4.2
Règles d’implémentation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
23
3.5
Groupes de sécurité . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
23
```

## Tableau 19 — admin-ad, page 4

### Docling

| 1 Introduction                                                    | 1 Introduction                                                                     | 1 Introduction                                                                          | 5                 |
|-------------------------------------------------------------------|------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|-------------------|
| 1.1                                                               | Objectif . . .                                                                     | du guide . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .              | . . . 5           |
| 1.2                                                               |                                                                                    | Organisation du guide . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . | . . . 6           |
| 1.3                                                               | . . .                                                                              | Conventions de lecture . . . . . . . . . . . . . . . . . . . . . . . . . . . . .        | . . . 7           |
| 1.4                                                               | Comment aborder ce                                                                 | guide? . . . . . . . . . . . . . . . . . . . . . . . . . . . . .                        | . . . 8           |
| 2 Méthodologie de cloisonnement logique de l'annuaire AD et du SI | 2 Méthodologie de cloisonnement logique de l'annuaire AD et du SI                  | 2 Méthodologie de cloisonnement logique de l'annuaire AD et du SI                       | 9                 |
| 2.1                                                               | Rappel                                                                             | des concepts fondamentaux de l'AD . . . . . . . . . . . . . . . . . . . . .             | . . . 9           |
| 2.2                                                               | Modèle de gestion des accès                                                        | privilégiés . . . . . . . . . . . . . . . . . . . . . . .                               | . . . 10          |
|                                                                   | 2.2.1 . . . .                                                                      | Choix dumodèle . . . . . . . . . . . . . . . . . . . . . . . . . . . .                  | . . . 12          |
|                                                                   | 2.2.2                                                                              | Mise en perspective dumodèle vis-à-vis des valeurs métiers . . . . . . . .              | . . . 15          |
|                                                                   | 2.2.3                                                                              | Enjeux de la mise enœuvre dumodèle . . . . . . . . . . . . . . . . . . .                | . . . 16          |
|                                                                   | 2.2.4                                                                              | Périmètre d'application dumodèle . . . . . . . . . . . . . . . . . . .                  | . . . 17          |
|                                                                   |                                                                                    | . . .                                                                                   |                   |
| 2.3                                                               | Le cloisonnement du SI en Tiers : un processus 2.3.1 Identification des périmètres | itératif . . . . . . . . . . . . . . . du Tier 0 et du Tier 1 . . . . . . . . . . . . . | . . . 19 . . . 21 |
|                                                                   | 2.3.2                                                                              | Analyse des chemins d'attaque . . . . . . . . . . . . . . . . . . . . . . . .           | . . . 21          |
|                                                                   | 2.3.3                                                                              | Catégorisation des ressources du SI en Tiers . . . . . . . . . . . . . . . . .          | . . . 23          |
|                                                                   | 2.3.4                                                                              | Application des bonnes pratiques d'administration du SI . . . . . . . . .               | . . . 25          |
|                                                                   | 2.3.5                                                                              | Application des bonnes pratiques d'architecture du SI . . . . . . . . . . .             | . . . 26          |
|                                                                   | 2.3.6                                                                              | Réduction de l'exposition de chaque Tier . . . . . . . . . . . . . . . . . .            | . . . 26          |
|                                                                   | 2.3.7                                                                              | Durcissement système et logiciel . . . . . . . . . . . . . . . . . . . . . . .          | . . . 28          |
|                                                                   | 2.3.8                                                                              | Délégation fine des droits . . . . . . . . . . . . . . . . . . . . . . . . . . .        | . . . 29          |
| 2.4                                                               |                                                                                    | Journalisation et détection . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . | . . . 30          |
| 3 Identification et cloisonnement du Tier 0                       | 3 Identification et cloisonnement du Tier 0                                        | 3 Identification et cloisonnement du Tier 0                                             | 32                |
| 3.1                                                               | Prérequis de sécurité . . . . . .                                                  | . . . . . . . . . . . . . . . . . . . . . . . . . . . .                                 | . . . 33          |
|                                                                   | 3.1.1                                                                              | Niveaux fonctionnels des forêts et domaines AD . . . . . . . . . . . . . .              | . . . 33          |
|                                                                   | 3.1.2                                                                              | Mise à jour des systèmes . . . . . . . . . . . . . . . . . . . . . . . . . . . .        | . . . 34          |
|                                                                   | 3.1.3                                                                              | Durcissement des systèmes . . . . . . . . . . . . . . . . . . . . . . . . . .           | . . . 35          |
| 3.2                                                               | Risques                                                                            | relatifs aux chemins de contrôle AD . . . . . . . . . . . . . . . . . . . .             | . . . 36          |
|                                                                   | 3.2.1                                                                              | Chemins de contrôle via les conteneurs système ou de configuration . . .                | . . . 38          |
|                                                                   | 3.2.2                                                                              | Chemins de contrôle par les comptes et groupes de sécurité intégrés par défaut          | 39                |
|                                                                   | 3.2.3                                                                              | Chemins de contrôle par les relations d'approbation . . . . . . . . . . . .             | . . . 40          |
|                                                                   |                                                                                    | 3.2.3.1 Relations d'approbation sortantes extraforêt . . . . . . . . . . . .            | . . . 40          |
|                                                                   |                                                                                    | 3.2.3.2 Relations d'approbation entrantes . . . . . . . . . . . . . . . . .             | . . . 42          |
|                                                                   | 3.2.4                                                                              | Outils d'analyse des chemins de contrôle AD . . . . . . . . . . . . . . . .             | . . . 43          |
|                                                                   |                                                                                    | 3.2.4.1 Outils d'analyse des chemins de contrôle AD utilisables en interne              | . . 43            |
|                                                                   |                                                                                    | 3.2.4.2 Service en ligne ADS de l'ANSSI . . . . . . . . . . . . . . . . . .             | . . . 44          |
| 3.3                                                               | Risques relatifs aux accès à des secrets d'authentification .                      | . . . . . . . . . . . .                                                                 | . . . 45          |
|                                                                   | 3.3.1                                                                              | Comptes d'administration locaux . . . . . . . . . . . . . . . . . . . . . . .           | . . . 47          |
|                                                                   | 3.3.2                                                                              | Secrets accessibles dans les scripts et les partages de fichiers . . . . . . . .        | . . . 48          |
|                                                                   | 3.3.3                                                                              | Comptes d'exécution des tâches planifiées et des services Windows . . . .               | . . . 50          |
|                                                                   | 3.3.4                                                                              | Secrets délivrés par des infrastructures de gestion de clés . . . . . . . . .           | . . . 51          |

### PyMuPDF (texte brut de la même zone)

```
1
Introduction
5
1.1
Objectif du guide . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
5
1.2
Organisation du guide . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
6
1.3
Conventions de lecture
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
7
1.4
Comment aborder ce guide?
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
8
2
Méthodologie de cloisonnement logique de l’annuaire AD et du SI
9
2.1
Rappel des concepts fondamentaux de l’AD . . . . . . . . . . . . . . . . . . . . . . . .
9
2.2
Modèle de gestion des accès privilégiés
. . . . . . . . . . . . . . . . . . . . . . . . . .
10
2.2.1
Choix du modèle . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
12
2.2.2
Mise en perspective du modèle vis-à-vis des valeurs métiers . . . . . . . . . . .
15
2.2.3
Enjeux de la mise en œuvre du modèle
. . . . . . . . . . . . . . . . . . . . . .
16
2.2.4
Périmètre d’application du modèle . . . . . . . . . . . . . . . . . . . . . . . . .
17
2.3
Le cloisonnement du SI en Tiers : un processus itératif . . . . . . . . . . . . . . . . . .
19
2.3.1
Identification des périmètres du Tier 0 et du Tier 1 . . . . . . . . . . . . . . . .
21
2.3.2
Analyse des chemins d’attaque
. . . . . . . . . . . . . . . . . . . . . . . . . . .
21
2.3.3
Catégorisation des ressources du SI en Tiers . . . . . . . . . . . . . . . . . . . .
23
2.3.4
Application des bonnes pratiques d’administration du SI
. . . . . . . . . . . .
25
2.3.5
Application des bonnes pratiques d’architecture du SI . . . . . . . . . . . . . .
26
2.3.6
Réduction de l’exposition de chaque Tier
. . . . . . . . . . . . . . . . . . . . .
26
2.3.7
Durcissement système et logiciel . . . . . . . . . . . . . . . . . . . . . . . . . .
28
2.3.8
Délégation fine des droits . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
29
2.4
Journalisation et détection
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
30
3
Identification et cloisonnement du Tier 0
32
3.1
Prérequis de sécurité . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
33
3.1.1
Niveaux fonctionnels des forêts et domaines AD . . . . . . . . . . . . . . . . .
33
3.1.2
Mise à jour des systèmes . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
34
3.1.3
Durcissement des systèmes
. . . . . . . . . . . . . . . . . . . . . . . . . . . . .
35
3.2
Risques relatifs aux chemins de contrôle AD
. . . . . . . . . . . . . . . . . . . . . . .
36
3.2.1
Chemins de contrôle via les conteneurs système ou de configuration . . . . . .
38
3.2.2
Chemins de contrôle par les comptes et groupes de sécurité intégrés par défaut 39
3.2.3
Chemins de contrôle par les relations d’approbation . . . . . . . . . . . . . . .
40
3.2.3.1
Relations d’approbation sortantes extraforêt . . . . . . . . . . . . . . .
40
3.2.3.2
Relations d’approbation entrantes
. . . . . . . . . . . . . . . . . . . .
42
3.2.4
Outils d’analyse des chemins de contrôle AD
. . . . . . . . . . . . . . . . . . .
43
3.2.4.1
Outils d’analyse des chemins de contrôle AD utilisables en interne . .
43
3.2.4.2
Service en ligne ADS de l’ANSSI
. . . . . . . . . . . . . . . . . . . . .
44
3.3
Risques relatifs aux accès à des secrets d’authentification . . . . . . . . . . . . . . . .
45
3.3.1
Comptes d’administration locaux . . . . . . . . . . . . . . . . . . . . . . . . . .
47
3.3.2
Secrets accessibles dans les scripts et les partages de fichiers . . . . . . . . . . .
48
3.3.3
Comptes d’exécution des tâches planifiées et des services Windows . . . . . . .
50
3.3.4
Secrets délivrés par des infrastructures de gestion de clés . . . . . . . . . . . .
51
```

## Tableau 20 — archi-si-sensibles, page 107

### Docling

| R35    | Durcir la configuration des matériels et des logiciels utilisés sur les SI sensibles   |   51 |
|--------|----------------------------------------------------------------------------------------|------|
| R36    | Marquer les informations sensibles                                                     |   52 |
| R37    | Marquer les supports stockant des informations sensibles                               |   53 |
| R38    | Adopter un code couleur pour le câblage des équipements                                |   53 |
| R39    | Activer une authentification initiale forte                                            |   54 |
| R40    | Protéger les secrets d'authentification                                                |   55 |
| R41    | Gérer avec rigueur l'affectation des droits d'accès logiques des comptes informatiques |   55 |
| R42    | Protéger le SI sensible des codes malveillants                                         |   56 |
| R43    | Adapter la politique de protection contre les codes malveillants                       |   56 |
| R44    | Déployer des outils révélant des activités suspectes                                   |   57 |
| R45    | Supports amovibles : limiter leur usage au strict besoin opérationnel                  |   58 |
| R46    | Supports amovibles : maîtriser leur gestion et leurs conditions d'usage                |   58 |
| R47    | Supports amovibles : privilégier l'utilisation de supports en lecture seule            |   59 |
| R48    | Supports amovibles : utiliser des solutions de dépollution des supports de stockage    |   60 |
| R49    | Maîtriser les moyens informatiques affectés aux utilisateurs d'un SI sensible          |   63 |
| R50    | Connecter les ressources sensibles sur un réseau physique dédié                        |   63 |
| R50-   | Connecter les ressources sensibles sur un réseau logique dédié                         |   64 |
| R51    | Authentifier les ressources sensibles vis-à-vis du réseau                              |   64 |
| R52    | Utiliser un poste utilisateur sensible dédié                                           |   65 |
| R52-   | Utiliser un poste utilisateur multiniveau                                              |   66 |
| R52- - | Utiliser un poste utilisateur sensible avec accès distant au SI usuel                  |   68 |
| R53    | Appliquer les recommandations de l'ANSSI relatives au nomadisme numérique              |   70 |
| R54    | Protéger physiquement les équipements d'accès nomade                                   |   71 |
| R55    | Sécuriser les canaux d'interconnexion nomades des SI DR                                |   71 |
| R56    | Sécuriser les canaux d'interconnexion nomades des SI sensibles                         |   71 |
| R57    | Chiffrer les données DR stockées sur des supports amovibles                            |   72 |
| R58    | Chiffrer les données sensibles stockées sur des supports amovibles                     |   72 |
| R59    | Chiffrer les flux réseau d'un équipement d'accès nomade sensible en toute circonstance |   73 |
| R60    | Mettre en place une architecture de réseau sans fil cloisonnée du SI sensible          |   74 |
| R61    | Bloquer l'accès aux portails captifs depuis des équipements d'accès nomades sensibles  |   74 |
| R62    | Appliquer les recommandations de l'ANSSI relatives à l'administration sécurisée des SI |   77 |
| R63    | Gérer les administrateurs d'un SI sensible                                             |   78 |
| R64    | Sécuriser la chaîne de connexion pour l'administration à distance                      |   83 |
| R64-   | Maîtriser les systèmes de télémaintenance connectés à des SI sensibles                 |   83 |
| R65    | Définir et appliquer une politique de MCS                                              |   84 |
| R66    | Isoler les systèmes obsolètes                                                          |   84 |
| R67    | Appliquer les recommandations de l'ANSSI relatives à la journalisation                 |   85 |
| R68    | Conserver les journaux d'un SI sensible pendant 12 mois                                |   85 |
| R69    | Recourir aux services d'un prestataire qualifié pour la supervision de sécurité        |   86 |
| R70    | Formaliser une procédure de déclaration des incidents de sécurité à l'ANSSI            |   86 |

### PyMuPDF (texte brut de la même zone)

```
R35
Durcir la configuration des matériels et des logiciels utilisés sur les SI sensibles
51
R36
Marquer les informations sensibles
52
R37
Marquer les supports stockant des informations sensibles
53
R38
Adopter un code couleur pour le câblage des équipements
53
R39
Activer une authentification initiale forte
54
R40
Protéger les secrets d’authentification
55
R41
Gérer avec rigueur l’affectation des droits d’accès logiques des comptes informatiques
55
R42
Protéger le SI sensible des codes malveillants
56
R43
Adapter la politique de protection contre les codes malveillants
56
R44
Déployer des outils révélant des activités suspectes
57
R45
Supports amovibles : limiter leur usage au strict besoin opérationnel
58
R46
Supports amovibles : maîtriser leur gestion et leurs conditions d’usage
58
R47
Supports amovibles : privilégier l’utilisation de supports en lecture seule
59
R48
Supports amovibles : utiliser des solutions de dépollution des supports de stockage
60
R49
Maîtriser les moyens informatiques affectés aux utilisateurs d’un SI sensible
63
R50
Connecter les ressources sensibles sur un réseau physique dédié
63
R50-
Connecter les ressources sensibles sur un réseau logique dédié
64
R51
Authentifier les ressources sensibles vis-à-vis du réseau
64
R52
Utiliser un poste utilisateur sensible dédié
65
R52-
Utiliser un poste utilisateur multiniveau
66
R52- -
Utiliser un poste utilisateur sensible avec accès distant au SI usuel
68
R53
Appliquer les recommandations de l’ANSSI relatives au nomadisme numérique
70
R54
Protéger physiquement les équipements d’accès nomade
71
R55
Sécuriser les canaux d’interconnexion nomades des SI DR
71
R56
Sécuriser les canaux d’interconnexion nomades des SI sensibles
71
R57
Chiffrer les données DR stockées sur des supports amovibles
72
R58
Chiffrer les données sensibles stockées sur des supports amovibles
72
R59
Chiffrer les flux réseau d’un équipement d’accès nomade sensible en toute circonstance
73
R60
Mettre en place une architecture de réseau sans fil cloisonnée du SI sensible
74
R61
Bloquer l’accès aux portails captifs depuis des équipements d’accès nomades sensibles
74
R62
Appliquer les recommandations de l’ANSSI relatives à l’administration sécurisée des SI
77
R63
Gérer les administrateurs d’un SI sensible
78
R64
Sécuriser la chaîne de connexion pour l’administration à distance
83
R64-
Maîtriser les systèmes de télémaintenance connectés à des SI sensibles
83
R65
Définir et appliquer une politique de MCS
84
R66
Isoler les systèmes obsolètes
84
R67
Appliquer les recommandations de l’ANSSI relatives à la journalisation
85
R68
Conserver les journaux d’un SI sensible pendant 12 mois
85
R69
Recourir aux services d’un prestataire qualifié pour la supervision de sécurité
86
R70
Formaliser une procédure de déclaration des incidents de sécurité à l’ANSSI
86
```
