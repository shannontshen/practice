import os
import sys
import subprocess
from argparse import ArgumentParser
from git import Repo, exc

CWD = os.path.abspath(os.path.dirname(__file__))
CONFIG = os.path.join(CWD, '..', 'ruff.toml')


class DiffLinter:
    def __init__(self, branch):
        self.branch = branch
        self.repo = Repo(os.path.join(CWD, '..'))
        self.head = self.repo.head.commit

    def get_branch_diff(self, uncommitted = False):
        """
            Determine the first common ancestor commit.
            Find diff between branch and FCA commit.
            Note: if `uncommitted` is set, check only
                  uncommitted changes
        """
        try:
            commit = self.repo.merge_base(self.branch, self.head)[0]
        except exc.GitCommandError:
            print(f"Branch with name `{self.branch}` does not exist")
            sys.exit(1)

        exclude = []  # previously needed by pycodestyle
        if uncommitted:
            diff = self.repo.git.diff(
                self.head, '--unified=0', '***.py', *exclude
            )
        else:
            diff = self.repo.git.diff(
                commit, self.head, '--unified=0', '***.py', *exclude
            )
        return diff

    def run_ruff(self):
        """
            Original Author: Josh Wilson (@person142)
            Source:
              https://github.com/scipy/scipy/blob/main/tools/lint_diff.py
            Unlike pycodestyle, ruff by itself is not capable of limiting
            its output to the given diff.
        """
        res = subprocess.run(
            ['ruff', 'check', '--statistics', '--config', CONFIG],
            stdout=subprocess.PIPE,
            encoding='utf-8',
        )
        return res.returncode, res.stdout


    def run_lint(self, uncommitted):
        retcode, errors = self.run_ruff()

        errors and print(errors)

        sys.exit(retcode)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--branch", type=str, default='main',
                        help="The branch to diff against")
    parser.add_argument("--uncommitted", action='store_true',
                        help="Check only uncommitted changes")
    args = parser.parse_args()

    DiffLinter(args.branch).run_lint(args.uncommitted)
