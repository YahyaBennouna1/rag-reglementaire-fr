"""Annotations des cas de validation du juge, et phrases piégées (fausses exprès).

    uv run python scripts/judge_annotations.py

Écrit data/eval/judge_labels.jsonl et ajoute les pièges à data/eval/judge_cases.jsonl.
Annotations RÉALISÉES PAR LLM (QUI DEVAIENT ÊTRE RÉALISÉES PAR MOI), à relire avec
scripts/review_judge_cases.py (champ « relu »).

Pour un piège, l'étiquette est certaine par construction : la phrase a été faussée exprès
à partir d'une phrase soutenue, avec les mêmes passages.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "eval" / "judge_cases.jsonl"
LABELS = ROOT / "data" / "eval" / "judge_labels.jsonl"

# Phrases réelles du système : toutes « soutenu », sauf celles-ci (raison donnée).
NOT_SUPPORTED_SYSTEM = {
    "q0187-s5": (
        "partiel",
        "mélange deux sortes de postes de rebond : navigation Web (détruits après usage) et "
        "administration dans le cloud (supprimés et réinstanciés régulièrement)",
    ),
    "q0192-s1": (
        "partiel",
        "« en continu » n'est pas dans le passage, et le passage dit que la remédiation peut « par "
        "exemple » être menée par des prestataires qualifiés, pas qu'elle l'est",
    ),
}

# (cas d'origine, phrase faussée, étiquette, ce qui a été faussé)
TRAPS = [
    ("q0128-s1", "Le code hexadécimal associé au groupe secp384r1 est 0x0019.", "non_soutenu", "chiffre"),
    (
        "q0182-s1",
        "Le nombre de groupes dont un utilisateur est membre ne peut pas excéder 2048 sous peine "
        "d'empêcher l'ouverture de session Windows.",
        "non_soutenu",
        "chiffre",
    ),
    (
        "q0182-s2",
        "La taille maximale du ticket Kerberos est passée à 16000 octets depuis Windows 2000 SP2.",
        "non_soutenu",
        "chiffre",
    ),
    (
        "q0007-s1",
        "Les ressources du Tier 0 ne doivent jamais exiger la signature SMB.",
        "non_soutenu",
        "négation",
    ),
    (
        "q0006-s1",
        "L'utilisation de WDRCG est fortement recommandée dans une démarche de défense en profondeur.",
        "non_soutenu",
        "négation",
    ),
    (
        "q0124-s1",
        "L'exigence SecNumCloud qui impose de fournir la liste de tous les droits d'accès d'un "
        "utilisateur donné est la 9.4b.",
        "non_soutenu",
        "mauvaise référence",
    ),
    (
        "q0127-s1",
        "Pour les opérations de ticket de service Kerberos, il est recommandé de ne pas activer d'audit.",
        "non_soutenu",
        "négation",
    ),
    (
        "q0129-s1",
        "Dans la version actuelle, la recommandation R12 a remplacé l'ancienne recommandation R11.",
        "non_soutenu",
        "mauvaise référence",
    ),
    (
        "q0184-s1",
        "Lors de l'installation d'un serveur Windows, s'il est prévu d'utiliser RDP, il est recommandé "
        "de désactiver l'authentification au niveau réseau (NLA).",
        "non_soutenu",
        "négation",
    ),
    (
        "q0018-s1",
        "Le cloisonnement des trois environnements d'entraînement, de déploiement et de production est "
        "facultatif, car les populations qui y ont accès sont généralement les mêmes.",
        "non_soutenu",
        "inversion",
    ),
    (
        "q0243-s1",
        "Le client VPN peut être lancé automatiquement après l'ouverture de session utilisateur, mode "
        "appelé parfois device tunnel.",
        "non_soutenu",
        "inversion",
    ),
    (
        "q0251-s1",
        "L'installation du service sysmon se caractérise par la copie du binaire sysmon.exe dans le "
        "dossier C:\\Program Files\\.",
        "non_soutenu",
        "mauvais terme",
    ),
    (
        "q0252-s1",
        "Le cumul des rôles de gestion de crise, de pilotage de l'investigation et de pilotage de la "
        "remédiation par une même personne est recommandé pour un incident d'ampleur.",
        "non_soutenu",
        "inversion",
    ),
    (
        "q0003-s1",
        "L'authentification 3 ne peut être réalisée qu'au moyen d'un serveur Active Directory.",
        "non_soutenu",
        "généralisation",
    ),
    (
        "q0001-s1",
        "En cas de centralisation complète d'un journal, sa taille idéale dépend du volume d'évènements "
        "et de la réglementation en termes de durée de conservation.",
        "non_soutenu",
        "mauvaise condition",
    ),
    (
        "q0123-s1",
        "Si le protocole TLS est mis en œuvre, le prestataire doit appliquer les recommandations de "
        "[NT_IPSEC].",
        "non_soutenu",
        "mauvaise référence",
    ),
    (
        "q0137-s1",
        "Selon l'exemple des processus utilisateurs, c'est le matériel physique qui agit comme moniteur "
        "de référence.",
        "non_soutenu",
        "mauvais terme",
    ),
    (
        "q0256-s1",
        "Il est important de configurer le pare-feu local Windows pour autoriser toutes les machines à "
        "se connecter à distance.",
        "non_soutenu",
        "inversion",
    ),
    (
        "q0012-s1",
        "L'utilisation d'un boîtier matériel d'acquisition vidéo unidirectionnelle entre les deux postes "
        "garantit une rupture protocolaire, à condition qu'il soit certifié EAL4+.",
        "partiel",
        "ajout inventé",
    ),
    (
        "q0014-s1",
        "Les efforts sont concentrés sur la limitation des escalades et des impacts, ce qui divise par "
        "deux le coût de la remédiation.",
        "partiel",
        "ajout inventé",
    ),
]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def main() -> None:
    cases = [c for c in read_jsonl(CASES) if c["origine"] == "systeme"]  # relançable sans doublons
    by_id = {c["id"]: c for c in cases}
    labels = []
    for case in cases:
        label, reason = NOT_SUPPORTED_SYSTEM.get(case["id"], ("soutenu", "le passage dit la même chose"))
        labels.append({"id": case["id"], "etiquette": label, "raison": reason, "relu": False})

    for n, (source_id, phrase, label, kind) in enumerate(TRAPS, start=1):
        trap_id = f"piege-{n:02d}"
        source = by_id[source_id]
        cases.append(
            {
                "id": trap_id,
                "question": source["question"],
                "phrase": phrase,
                "passages": source["passages"],
                "origine": "piege",
            }
        )
        labels.append({"id": trap_id, "etiquette": label, "raison": f"piège : {kind}", "relu": False})

    write_jsonl(CASES, cases)
    write_jsonl(LABELS, labels)
    print(f"{len(cases)} cas, dont {len(TRAPS)} pièges -> {LABELS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
