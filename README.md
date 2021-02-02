# snyk-exercise

## Notes to the reader

This project is not in a complete or working state. It is very much a work in progress, and should be approached with caution. 

## Architecture
The project consists of a Python web app, that is deployed using Flask. It relies on HTML and CSS for display and formatting. It uses a local SQL database for caching dependencies once they have been retrieved.

When a new dependency tree is requested, the following process takes place:

The dependencies of the package are retrieved. If they are cached in the local DB (matching name and version), then they are fetched from there. Otherwise a call is made to the npm repo, and they are retrieved.

The dependency list is then walked (breath first) to recurrsively repeat this process for each dependency package, finding it's subdependencies. Each new dependency is added to the end of the list. 

Finally (not implemented) This info will be constructed into a linked tree, to display the information.

The home page (/) shows a printout of the current local DB, including all dependencies fetched.

The /request page allows a user to input a library name and version for information gathering.

The /results page displays the results of the search.

## Assumptions & Notes
The project is intended as a simple PoC, and as such is not intended for re-use elsewhere. Therefore it does not have an OSS license attached.

Due to the difficulty of parsing the various formats for version numbers, the versions are treated as text strings. This prevents any ordering processing, and intelligent parsing of items such as 'latest'.

For the webapp to pass information between pages, it relies on a SecretKey. This is not committed to the repo, and each deployment would need to generate a unique random Key. 

The python code is written to be functional, but almost certainly does not follow many naming convections and other style choices. These should be fixed at a later stage of development.

The DB is not secured. This is for ease of use at this stage of the project, but would need to be addressed later.

The web page itself (including the user input) is not secured, and does not have any input sanitization.

To deploy the app, the Flask binary needs to be in the path. The Flask environment is currently only tested in development mode (FLASK_ENV = development) and the app needs to be set to 'app' (FLASK_APP = app). Finally, it is run with 'flask run'.

## Unfinished Tasks
The current list of dependencies is constructed as an unordered, unlinked list. This needs to be updated to produce a tree.

Version numbers are treated as text strings, rather than as values.

Versioning information such as >, ~ are ignored.

Hits against the DB are treated as hits regardless of their age. This needs to be updated to be re-fetched if the data is stale.

A lot of error handling is not present. If packages (either provided by a user or listed as a dependency) are not matches, this is not handled. 

The code needs tidying up in many places. It has been written to implement the basic functionality, with each function being layered on top. Once it is in a reasonably functioning state - at least handling the happy day scenario - it should be refactored to enable it to be better maintained. 

No coding style was followed, and some C/C++ style conventions have been followed, rather than the appropriate python ones.

The SQL requests are all hand formed, and as such are not maintainable. This functionality should be put into a dedicated set of functions to construct the messages in a much cleaner way.

Output formatting is very crude. This should be update.
