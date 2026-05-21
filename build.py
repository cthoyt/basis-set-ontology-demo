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

HERE = Path(__file__).parent.resolve()

VERSION = "0.12"


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

    prefix = "OTC"
    header_1 = ("identifier", "type", "label", "abbreviation", "parent")
    header_2 = (
        "ID",
        "TYPE",
        "AT rdfs:label^^xsd:string",
        "AT oboInOwl:hasExactSynonym^^xsd:string",
        "SC %",
    )
    rows = [
        header_2,
        (f"{prefix}:0000001", "owl:Class", "role", "", ""),
        (f"{prefix}:0000002", "owl:Class", "family", "", ""),
        (f"{prefix}:0000003", "owl:Class", "function type", "", ""),
        (f"{prefix}:0000004", "owl:Class", "basis set", "", ""),
    ]
    click.echo(
        f"Roles:\n\n{tabulate(role_counter.most_common(), headers=['role', 'count'], tablefmt='github')}"
    )
    counter = 5
    for role in role_counter:
        rows.append(
            (
                f"{prefix}:{counter:07}",
                "owl:Class",
                NAMES.get(role),
                role,
                f"{prefix}:0000001",
            )
        )
        counter += 1
    click.echo(
        f"\n\nFamilies:\n\n{tabulate(family_counter.most_common(), headers=['family', 'count'], tablefmt='github')}"
    )
    for family in family_counter:
        rows.append(
            (
                f"{prefix}:{counter:07}",
                "owl:Class",
                NAMES.get(family),
                family,
                f"{prefix}:0000002",
            )
        )
        counter += 1
    click.echo(
        f"\n\nFunction Types:\n\n{tabulate(function_type_counter.most_common(), headers=['function type', 'count'], tablefmt='github')}"
    )
    for function_type in function_type_counter:
        rows.append(
            (
                f"{prefix}:{counter:07}",
                "owl:Class",
                NAMES.get(function_type),
                function_type,
                f"{prefix}:0000003",
            )
        )
        counter += 1

    for basis_set in basis_sets:
        rows.append(
            (
                f"{prefix}:{counter:07}",
                "owl:Class",
                NAMES.get(basis_set.name),
                basis_set.name,
                f"{prefix}:0000004",
            )
        )
        counter += 1

    pd.DataFrame(rows, columns=header_1).to_csv("terms.tsv", sep="\t", index=False)
    os.system(
        'robot template --prefix "OTC: http://purl.obolibrary.org/obo/OTC_" --template terms.tsv --output otc.owl'
    )


if __name__ == "__main__":
    main()
