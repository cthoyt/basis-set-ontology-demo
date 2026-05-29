# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "click>=8.4.0",
#     "pyobo>=0.12.22",
#     "pystow>=0.8.13",
#     "requests>=2.34.2",
# ]
# ///

import os
import pandas as pd
from pydantic import BaseModel
import pystow
from tabulate import tabulate
import click
from collections import Counter
from tqdm import tqdm
import tarfile
import json
from pathlib import Path

PREFIX = "BSEO"  # basis set exchange ontology
VERSION = "0.12"

HERE = Path(__file__).parent.resolve()
TMP = HERE / "tmp"
TMP.mkdir(parents=True, exist_ok=True)

manual_output = TMP.joinpath("manual.owl")
automatic_output = TMP.joinpath("automatic.owl")
final_output = HERE.joinpath(PREFIX.lower()).with_suffix(".owl")


class BasisSet(BaseModel):
    name: str
    role: str
    description: str
    family: str
    function_types: list[str]


NAMES = {
    "gto": "Gaussian-type orbitals",
    "gto_spherical": "spherical Gaussian-type orbitals",
    "gto_cartesian": "cartesian Gaussian-type orbitals",
    "scalar_ecp": "scalar effective core potentials",
}


@click.command()
def main() -> None:
    url = f"https://www.basissetexchange.org/static/archives/{VERSION}/basis_sets-json-{VERSION}.tar.bz2"
    path = pystow.ensure("bio", "basis-set-exchange", url=url)
    basis_sets = []
    with tarfile.open(path) as tf:
        for member in tqdm(tf, unit="file"):
            if not member.name.endswith(".json"):
                continue
            with tf.extractfile(member) as file:
                data = json.load(file)
            bs = BasisSet.model_validate(data)
            basis_sets.append(bs)

    role_counter = Counter()
    family_counter = Counter()
    function_type_counter = Counter()
    for basis_set in basis_sets:
        role_counter[basis_set.role] += 1
        family_counter[basis_set.family] += 1
        for function_type in basis_set.function_types:
            function_type_counter[function_type] += 1

    write = False

    header_1 = (
        "identifier",
        "type",
        "label",
        "abbreviation",
        "parent",
        'description',
        "has role",
        "has family",
        "has function type",
    )
    header_2 = (
        "ID",
        "TYPE",
        "AT rdfs:label^^xsd:string",
        "AT oboInOwl:hasExactSynonym^^xsd:string",
        "SC %",
        "AT dc:description^^xsd:string",
        "SC BSEO:0100000",
        "SC BSEO:0100001",
        "SC BSEO:0100002 SPLIT=|",
    )
    rows = [
        header_2,
        (f"{PREFIX}:0000005", "owl:Class", "ANO basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000006", "owl:Class", "ANO-RCC basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000007", "owl:Class", "STO basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000008", "owl:Class", "seg-cc basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000009", "owl:Class", "SBO4 basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000010", "owl:Class", "saug-ano basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000011", "owl:Class", "SARC2-QZVP basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000012", "owl:Class", "SARC2-QZV basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000013", "owl:Class", "Sapporo-TZP basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000014", "owl:Class", "Sapporo-QZP basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000015", "owl:Class", "Sapporo-DZP basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000016", "owl:Class", "Sapporo-DKH3 basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000017", "owl:Class", "pob basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000018", "owl:Class", "pcSseg basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000019", "owl:Class", "pcseg basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000020", "owl:Class", "pcS basis set", "", f"{PREFIX}:0000004", ""),
        (f"{PREFIX}:0000021", "owl:Class", "pcJ basis set", "", f"{PREFIX}:0000004", ""),
    ]
    if write:
        click.echo(
            f"Roles:\n\n{tabulate(role_counter.most_common(), headers=['role', 'count'], tablefmt='github')}"
        )
    counter = 5
    role_to_curie = {}
    for role in role_counter:
        role_curie = f"{PREFIX}:0001{counter:03}"
        role_to_curie[role] = role_curie
        rows.append(
            (
                role_curie,
                "owl:Class",
                NAMES.get(role, role),
                "",
                f"{PREFIX}:0000001",
                "",  # description
                "",  # role
                "",  # family
                "",  # function type
            )
        )
        counter += 1

    if write:
        click.echo(
            f"\n\nFamilies:\n\n{tabulate(family_counter.most_common(), headers=['family', 'count'], tablefmt='github')}"
        )
    family_to_curie = {}
    for family in family_counter:
        family_curie = f"{PREFIX}:0002{counter:03}"
        family_to_curie[family] = family_curie
        rows.append(
            (
                family_curie,
                "owl:Class",
                NAMES.get(family, family),
                "",
                f"{PREFIX}:0000002",
                "",  # description
                "",  # role
                "",  # family
                "",  # function type
            )
        )
        counter += 1
    if write:
        click.echo(
            f"\n\nFunction Types:\n\n{tabulate(function_type_counter.most_common(), headers=['function type', 'count'], tablefmt='github')}"
        )
    function_type_to_curie = {}
    for function_type in function_type_counter:
        function_type_curie = f"{PREFIX}:0003{counter:03}"
        function_type_to_curie[function_type] = function_type_curie
        rows.append(
            (
                function_type_curie,
                "owl:Class",
                NAMES.get(function_type, function_type),
                "",
                f"{PREFIX}:0000003",
                "",  # description
                "",  # role
                "",  # family
                "",  # function type
            )
        )
        counter += 1

    parent_names = [
        ("ANO-RCC", f"{PREFIX}:0000006"),
        ("ANO-", f"{PREFIX}:0000005"),
        ("STO-", f"{PREFIX}:0000007"),
        ("seg-cc-", f"{PREFIX}:0000008"),
        ("SBO4-", f"{PREFIX}:0000009"),
        ("saug-ano-", f"{PREFIX}:0000010"),
        ("SARC2-QZVP-", f"{PREFIX}:0000011"),
        ("SARC2-QZV-", f"{PREFIX}:0000012"),
        ("Sapporo-TZP-", f"{PREFIX}:0000013"),
        ("Sapporo-QZP-", f"{PREFIX}:0000014"),
        ("Sapporo-DZP-", f"{PREFIX}:0000015"),
        ("Sapporo-DKH3-", f"{PREFIX}:0000016"),
        ("pob-", f"{PREFIX}:0000017"),
        ("pcSseg-", f"{PREFIX}:0000018"),
        ("pcseg-", f"{PREFIX}:0000019"),
        ("pcS-", f"{PREFIX}:0000020"),
        ("pcJ-", f"{PREFIX}:0000021"),
    ]

    seen = set()

    for basis_set in basis_sets:
        if basis_set.name.strip() in seen:
            continue  # FIXME why are there duplicates?
        seen.add(basis_set.name.strip())

        # TODO understand internal structure
        basis_set.name.split("-")

        for name_prefix, parent_curie in parent_names:
            if basis_set.name.startswith(name_prefix):
                parent = parent_curie
                break
        else:
            if write:
                tqdm.write(f"no parent for {basis_set.name}")
            parent = f"{PREFIX}:0000004"

        rows.append(
            (
                f"{PREFIX}:{counter:07}",
                "owl:Class",
                NAMES.get(basis_set.name, basis_set.name),  # TODO require all have proper names
                basis_set.name,
                parent,
                basis_set.description if basis_set.description != basis_set.name else "",
                role_to_curie[basis_set.role],
                family_to_curie[basis_set.family],
                "|".join(function_type_to_curie[f] for f in basis_set.function_types or []),
            )
        )
        counter += 1

    pd.DataFrame(rows, columns=header_1).to_csv("terms.tsv", sep="\t", index=False)
    robot()

def robot():
    os.system(
        f"robot template "
        f'--prefix "{PREFIX}: http://purl.obolibrary.org/obo/{PREFIX}_" '
        f"--template terms-manual.tsv "
        f"--output {manual_output.as_posix()}"
    )
    os.system(
        f"robot template "
        f'--prefix "{PREFIX}: http://purl.obolibrary.org/obo/{PREFIX}_" '
        f"--template terms.tsv "
        f"--output {automatic_output}"
    )
    os.system(
        f"robot merge "
        f"--input {manual_output} "
        f"--input {automatic_output} "
        "annotate "
        f'--ontology-iri "http://purl.obolibrary.org/obo/{PREFIX.lower()}.owl" '
        f"--output {final_output}")


if __name__ == "__main__":
    main()
