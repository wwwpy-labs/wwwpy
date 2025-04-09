import js


def setup():
    js.document.head.insertAdjacentHTML('beforeend', simple_dark_theme_header)


# language=html
simple_dark_theme_header = """
<link rel="icon" href="data:,">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    :root {
        color-scheme: dark;
    }
    
    body {
        background: #121212;
        color: #e0e0e0;
        margin: 1rem;
        font: 16px sans-serif;
        line-height: 1.5;
    }

    a {
        color: #bb86fc;
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }

    button, 
    input[type="button"], 
    input[type="submit"] {
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 4px;
        font-size: 1rem;
        cursor: pointer;
        transition: background-color 0.2s;
        min-height: 40px;
    }

    button:hover, 
    input[type="button"]:hover, 
    input[type="submit"]:hover {
        background-color: #6200ee;
    }
    
    input[type="text"], 
    input[type="email"], 
    input[type="password"],
    input[type="number"],
    textarea {
        background-color: #1e1e1e;
        color: #ffffff;
        border: 1px solid #333;
        border-radius: 4px;
        padding: 0.5rem;
        font-size: 1rem;
        min-height: 40px;
        box-sizing: border-box;
        width: 100%;
    }

    select {
        border: 1px solid #333;
        border-radius: 4px;
        padding: 0.5rem;
        font-size: 1rem;
        min-height: 40px;
        width: 100%;
        appearance: none;
        background-image: url("data:image/svg+xml;utf8,<svg fill='white' height='24' width='24' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/></svg>");
        background-repeat: no-repeat;
        background-position: right 0.5rem center;
        padding-right: 2rem;
    }

    input:focus, 
    select:focus, 
    textarea:focus {
        outline: none;
        border-color: #bb86fc;
    }

    /* Basic form layout */
    form {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        max-width: 500px;
    }

    label {
        font-weight: bold;
        margin-bottom: 0.25rem;
        display: block;
    }

    /* Checkbox and radio styling */
    input[type="checkbox"],
    input[type="radio"] {
        accent-color: #bb86fc;
        margin-right: 0.5rem;
    }

    /* Table styling */
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1rem 0;
    }

    th, td {
        padding: 0.75rem;
        text-align: left;
        border-bottom: 1px solid #333;
    }

    th {
        background-color: #1e1e1e;
    }

    tr:hover {
        background-color: #1e1e1e;
    }
</style>
"""
