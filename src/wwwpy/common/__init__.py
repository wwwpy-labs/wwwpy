_no_remote_infrastructure_found_text = """
Import of package "remote" failed. Unable to bootstrap the application."""

# language=html
_remote_module_not_found_html = """
Warning, no module 'remote' was found.
<br>
<br>
This may be because the running directory is not a valid wwwpy project directory.
<br>
<br>
If you want to create a new project from the quickstarter, be sure to run from an <i>empty</i> directory.
<br>
Read for more information about the 
 <a href="https://github.com/wwwpy-labs/wwwpy/blob/main/docs/introduction.md#quickstart-in-dev-mode" target='_blank'>
 quickstarter</a> and a 
 <a href="https://github.com/wwwpy-labs/wwwpy/blob/main/docs/introduction.md#a-wwwpy-project-structure" target='_blank'>
 general project structure.</a>
"""
_warn = '\033[33m[WARN]\033[0m'
_remote_module_not_found_console = f"""{_warn} The current project folder is not empty: $[directory]  
{_warn} It does not contain a `remote` package, which is required for a wwwpy project.  
If you want to create a new project from the quickstarter, be sure to run from an empty directory.
Read for more information here: https://github.com/wwwpy-labs/wwwpy/blob/main/docs/introduction.md"""
