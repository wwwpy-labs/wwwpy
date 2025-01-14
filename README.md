# wwwpy

[python_versions]: https://img.shields.io/pypi/pyversions/wwwpy.svg?logo=python&logoColor=white

[![Test suite](https://github.com/wwwpy-labs/wwwpy/actions/workflows/ci.yml/badge.svg)](https://github.com/wwwpy-labs/wwwpy/actions/workflows/ci.yml)
![PyPI](https://img.shields.io/pypi/v/wwwpy)
[![Python Versions][python_versions]](https://pypi.org/project/wwwpy/)


Develop web applications in Python quickly and easily.

The vision of wwwpy:

Simplify the learning curve and accelerate the development process. Make the development experience intuitive so developers can quickly move from understanding to implementation, solving problems faster. ⚡

- ✨ Jumpstart Your Projects: With just a couple of commands, get a head start on building web UIs, allowing you to focus on coding and scaling your application.
- 💻 Build Web UIs: Create web interfaces without focusing (too much :P) on the front end. Everything is Python. You can avoid HTML/DOM/CSS/JavaScript, but you can use its full power if you want. Use the drag-and-drop UI builder for rapid prototyping while still being able to easily create, extend, and customize UIs as needed.
- 🏗️ Integrated Development Environment: use an intuitive UI building experience within the development environment, making it easy to edit properties and components as you go.
- 🔗 Direct Code Integration: UI components are fully reflected in the source code, allowing manual edits. Every change is versionable and seamlessly integrates with your source code repository.
- 🔄 Hot reload: Any change to the source code is immediately reflected in the running application when in dev-mode.
- 🖥️ Client-server: Call server-side functions from the browser seamlessly without writing API endpoints. You can also call the browser(s) from the server to push changes and information to it.
- 📈 Versatile Scalability: From quick UI prototypes to large-scale enterprise applications, wwwpy handles everything from simple interfaces to complex projects with external dependencies and integrations.


# How to Use

### Installation

```
pip install wwwpy
```

### Getting Started
To start developing:

```
mkdir my_project
cd my_project

wwwpy dev
```

If the project folder is [**_empty_**](https://github.com/wwwpy-labs/wwwpy/blob/main/docs/introduction.md#quickstart-in-dev-mode), wwwpy will ask you to select a quickstart project to help you explore its features right away.

Explore the available command line options in the [CLI usage guide](https://github.com/wwwpy-labs/wwwpy/blob/main/docs/cli_usage.md).


## Documentation

* [Introduction](https://github.com/wwwpy-labs/wwwpy/blob/main/docs/introduction.md): Learn about the project structure and how to get started.
* [Component Documentation](https://github.com/wwwpy-labs/wwwpy/blob/main/docs/component.md): Instructions on how to use and create components.
* [Seamless communication between server and browser(s)](https://github.com/wwwpy-labs/wwwpy/blob/main/docs/rpc.md): Learn about seamless communication between the server and browser(s).
* [CLI usage guide](https://github.com/wwwpy-labs/wwwpy/blob/main/docs/cli_usage.md).

## Roadmap
Our primary focus is to get to know how you are using wwwpy and what are the problems you are solving now or trying to solve. 
Please, reach out to us and share your experience.

Disclaimer: This roadmap is fluid and we will change according to your feedback. If you have comments or ideas, please open an issue or post a message in a discussion.

- Add support for [Plotly](https://plotly.com/javascript/)
- Add support for [AG Grid](https://ag-grid.com) 
- Easy integration with Django, FastAPI and other Python web frameworks (add support for ASGI)
- Create a database quickstart with vanilla SQLite (or SQLAlchemy)
- Develop a flexible and extensible data-binding mechanism
- Implement a simple layout system to easily place components
- Add support for Ionic custom web components
- Documentation and tutorial about keybindings (hotkey and shortcuts)
- PyCharm and VS Code plugin
- Execute/Schedule server-side code [see issue](https://github.com/wwwpy-labs/wwwpy/issues/3)
- Support IDE Python completion for shoelace property (through Python stubs .pyi)
- Improve the serialization mechanism of RPC
- Change the default event handler code from 'console.log' to 'logger.debug' to use the Python API. As a side effect, all the logging is sent to the server console (only in dev-mode)
- Improve and clean the Component API that handle the shadow DOM
- Add a cute loader instead of the plain `<h1>Loading...</h1>`
- Other ideas? Please, chime in and let us know.


### Toolbox improvements:
- Improve the selection mechanism; it should be smarter and 'do the right thing' given the context
- Implement the deletion of an element
- Give better visibility to "Create new Component" and "Explore local filesystem"; now they are at the bottom of the item list
- "Create new Component" should ask for the name of the component and additional information
- Develop a 'manual' element selection for those element not easily selected with the mouse
- Implement the rename of an element
- Dynamically include the user custom Components in the palette so they can be dropped and used
- When creating event handlers, add type hints to the event parameter, e.g., `def button1__click(self, event: js.MouseEvent)`
- Setting the data-name should declare the Python definition
- Removing the data-name should remove the Python definition
- Improve the editing of third-party components (e.g., shoelace). Some components have constraints on parents or children, facilitate that (also standard elements have constraints like this).

