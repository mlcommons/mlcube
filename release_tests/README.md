# MLCommons-Box Release process


Hard requirements:
1. Versions of all projects must be the same, e.g. 0.2.3. This applies to [mlcommons_box](https://github.com/mlperf/mlbox/tree/master/mlcommons_box)
   and to all [runners](https://github.com/mlperf/mlbox/tree/master/runners).
2. All runners depend on mlcommons_box library. Version in each requirements.txt file must equal and be the version of
   current release. If current release version is 0.2.3, then all runners must specify mlcommons-box==0.2.3 in their
   respective requirements files. 
3. New MLCommons-Box packages are automatically pushed to PyPi when a new release is created on GitHub. 
3. Currently, only a limited number of people can make a new release (Subin and Sergey have permissions to push new
   packages to PyPi). 


Check list before making a new release:
1. Figure out the version of the [last release](https://pypi.org/project/mlcommons-box/) and make sure the current
   version has been set to the right value for all projects and their dependencies. All package versions and their
   dependencies must be the same (== current release version). Check the following:
   - MLCommons-Box version in [setup.py](https://github.com/mlperf/mlbox/blob/master/mlcommons_box/setup.py).
   - For [each runner](https://github.com/mlperf/mlbox/tree/master/runners) check their setup.py and requirements.txt
     files.
2. Projects' unit tests. They run for each PR, so it is assumed all init tests are OK.
3. Run extended (release) unit tests for each runner. This requires special software stack, such as docker or
   singularity. Runners such as SSH, K8S and GCP require more complex user environment.
   > TODO: DOCUMENT REQUIRED ENVIRONMENTS TO TEST EACH RUNNER    


Proposed semi-automated workflow:
1. Clone the latest master branch.
2. Create a new branch off the master branch, let's say, `bugfix/release-0.2.3`, in case project updates will be
   required.
3. Run release unit tests. Not all tests run. Each test will try to figure out if user environment is appropriate for
   running runners' unit tests. Run them as follows:
   ```
   python -m unittest discover release_tests/
   ```
   Some of the tests will check things like project versions and will re-run projects' unit tests.
   > TODO: The release tests are Work In Progress.
4. If something fails, fix and go to #3.
5. If updates are required, commit, push and create a new PR. Once merged, repeat all steps above.
6. Make a GitHub release (what will also push packages to PyPi):
   - Go to MLBox GitHub [repo](https://github.com/mlperf/mlbox) and click [Releases](https://github.com/mlperf/mlbox/releases)
     that you should see on the right, below the `About` section. If no `Releases` link is available, that probably
     means a user does not have appropriate rights to create releases.
   - Click `Draft a new release`.
   - The `Tag version` and `Release title` should be set to a new release version. Also, provide a release description.
   - Click `Publish release`.
     