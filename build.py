# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "click>=8.4.0",
#     "pyobo>=0.12.22",
#     "pystow>=0.8.13",
#     "requests>=2.34.2",
# ]
# ///

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

    click.echo(
        f"Roles:\n\n{tabulate(role_counter.most_common(), headers=['role', 'count'], tablefmt='github')}"
    )
    click.echo(
        f"\n\nFamilies:\n\n{tabulate(family_counter.most_common(), headers=['family', 'count'], tablefmt='github')}"
    )
    click.echo(
        f"\n\nFunction Types:\n\n{tabulate(function_type_counter.most_common(), headers=['function type', 'count'], tablefmt='github')}"
    )


if __name__ == "__main__":
    main()
