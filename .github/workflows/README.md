# GitHub Actions CI/CD docs

## docs-site action

The mkdocs action builds and deploys the documentation site into the `gh-pages` branch. For more details on the workflow spec, [docs-site.yml].

### How it works

The [mlcube repo](https://github.com/mlperf/mlcube) has Pull Requests pushed into the `master` branch on every merge. So the event associated with every PR merge is a `event:push`.

So the `docs-site` GitHub Action is triggered on every push into the repo. 

In the workflow spec,
```yaml
on:
  push:
```

We don't want the Action to be run on all commits because most changes aren't going to be related to documentation. To filter out and run the `docs-site` **only** on changes relevant to documentation, we set the `paths` field in the workflow. We trigger the Action on a `event:push` with changes to files inside the `docs/` directory or to the `docs-site` workflow.

```yaml
on:
  push:
    paths:
    - 'docs/**'
    - '.github/workflows/docs-site.yml'
```

In order to not fill-up space on the repo with the docs-site related files, the `docs-site` GitHub Action builds the `docs/` and commits them to the `gh-pages` branch.

```yaml
- name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3.5.6
        with:
          user_name: 'github-actions[bot]'
          user_email: 'github-actions[bot]@users.noreply.github.com'
          deploy_key: ${{ secrets.ACTIONS_DEPLOY_KEY }}
          publish_dir: ./site
          allow_empty_commit: true
```

### docs-site Action Development documentation

- Python version

    The GitHub Action uses a `python 3.6` environment. Please make changes to the workflow in this part to upgrade or downgrade python for the mkdocs site.
    ```yaml
    - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v2
        with:
          python-version: 3.6
    ``` 

- Dependencies

    The mkdocs is built with the dependencies held in [mkdocs-requirement.txt](../mkdocs-requirement.txt). If you wish to add mkdocs plugins or add dependencies, please make changes in that file.

- Permissions

    The `docs-site` GitHub Action uses a deploy key specifically created for it. To revoke access to the GitHub Action, delete the secret `ACTIONS_DEPLOY_KEY` in [Repository Settings](https://github.com/mlperf/mlcube/settings/secrets/).

## python-publish action

The python-publish action builds and publishes the python packages to PyPI. For more details on the workflow spec, [python-publish.yml].  
  Once the python-publish job completes it triggers Repository Dispatch Event which uses `MLCOMMONS_REPO_ACCESS` to trigger a event to the repositoy.
  ```yaml
    dispatch:
    needs: deploy
    runs-on: ubuntu-latest
    steps:
      - name: Repository Dispatch
        uses: peter-evans/repository-dispatch@v1
        with:
          token: ${{ secrets.MLCOMMONS_REPO_ACCESS }}
          repository: mlperf/mlcube
          event-type: publish-runners  
  ```
This event is captured by runner-publish action which builds and publishes all the runners packages to PyPI.
  ```yaml
    on:
    repository_dispatch:
      types: publish-runner`
  ```

More Information on python-publish action & Repository Dispatch action can be found here:
  - https://github.com/marketplace/actions/repository-dispatch
  - https://github.com/marketplace/actions/pypi-publish

### Secrets used
| Name  |   |
|---|---|
|PYPI_USER        |pypi login credentials used in GitHub workflows    |
|PYPI_PASSWORD    |pypi login credentials used in GitHub workflows    |
|MLCOMMONS_REPO_ACCESS   |public_repo ACL for request dispatch in GitHub workflows  |
