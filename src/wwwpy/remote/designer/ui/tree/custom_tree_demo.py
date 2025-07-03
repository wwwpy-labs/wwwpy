import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js
from wwwpy.remote.designer.ui.tree.custom_tree import TreeElement, ItemPresentation, CustomTree


# Helper to build TreeElement hierarchy from JSON
def createTreeFromJSON(json_node, parent=None):
    text = json_node.get('text', 'Unnamed')
    icon = json_node.get('icon', None)
    bg = json_node.get('backgroundColor', None)
    pres = ItemPresentation(text, icon, bg)
    element = None

    def loader():
        return [createTreeFromJSON(child, element) for child in json_node.get('children', [])]

    element = TreeElement(pres, loader, parent)
    return element


# Demo component that showcases the CustomTree usage
class CustomTreeDemo(wpc.Component, tag_name='custom-tree-demo'):
    fileTree: CustomTree = wpc.element()
    orgTree: CustomTree = wpc.element()

    def init_component(self):
        # attach shadow DOM and template
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        self.element.shadowRoot.innerHTML = """
<style>
    :host { display: block; }
    .tree-container { background: #161b22; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3); max-width: 600px; border: 1px solid #30363d; margin-bottom: 30px; }
    .demo-title { color: #f0f6fc; margin-bottom: 10px; font-size: 1.2em; }
</style>
<div class="demo-section">
    <h2 class="demo-title">File System Tree Example</h2>
    <div class="tree-container">
        <custom-tree data-name="fileTree"></custom-tree>
    </div>
</div>
<div class="demo-section">
    <h2 class="demo-title">Organization Tree Example</h2>
    <div class="tree-container">
        <custom-tree data-name="orgTree"></custom-tree>
    </div>
</div>
"""

    async def after_init_component(self):
        # JSON for file system tree
        fileSystemJSON = {
            'text': 'Project Root', 'icon': '📁',
            'children': [
                {'text': 'src', 'icon': '📁', 'children': [
                    {'text': 'components', 'icon': '📁', 'children': [
                        {'text': 'Button.js', 'icon': '📄'},
                        {'text': 'Modal.js', 'icon': '📄'},
                        {'text': 'Tree.js', 'icon': '📄', 'backgroundColor': '#3d2817'}
                    ]},
                    {'text': 'utils', 'icon': '📁', 'backgroundColor': '#2d4a22', 'children': [
                        {'text': 'helpers.js', 'icon': '📄'},
                        {'text': 'constants.js', 'icon': '📄'}
                    ]},
                    {'text': 'index.js', 'icon': '📄', 'backgroundColor': '#1f2937'}
                ]},
                {'text': 'public', 'icon': '📁', 'children': [
                    {'text': 'index.html', 'icon': '🌐'},
                    {'text': 'favicon.ico', 'icon': '🖼️', 'backgroundColor': '#4c1d95'}
                ]},
                {'text': 'package.json', 'icon': '📦'},
                {'text': 'README.md', 'icon': '📝'}
            ]
        }
        # JSON for organization tree
        organizationJSON = {
            'text': 'TechCorp Inc.', 'icon': '🏢', 'backgroundColor': '#1e293b',
            'children': [
                {'text': 'Engineering', 'icon': '⚙️', 'backgroundColor': '#1f2937', 'children': [
                    {'text': 'Frontend Team', 'icon': '💻', 'children': [
                        {'text': 'Alice Johnson - Lead', 'icon': '👤', 'backgroundColor': '#7c2d12'},
                        {'text': 'Bob Smith - Developer', 'icon': '👤'},
                        {'text': 'Carol Williams - Developer', 'icon': '👤'}
                    ]},
                    {'text': 'Backend Team', 'icon': '🔧', 'children': [
                        {'text': 'David Brown - Lead', 'icon': '👤', 'backgroundColor': '#7c2d12'},
                        {'text': 'Eva Davis - Developer', 'icon': '👤'}
                    ]}
                ]},
                {'text': 'Product', 'icon': '📊', 'backgroundColor': '#2d1b69', 'children': [
                    {'text': 'Sarah Wilson - Manager', 'icon': '👤', 'backgroundColor': '#7c2d12'},
                    {'text': 'Mike Chen - Designer', 'icon': '👤'}
                ]},
                {'text': 'Sales', 'icon': '💼', 'backgroundColor': '#14532d', 'children': [
                    {'text': 'Tom Anderson - Director', 'icon': '👤', 'backgroundColor': '#7c2d12'},
                    {'text': 'Lisa Garcia - Rep', 'icon': '👤'}
                ]}
            ]
        }
        # build trees
        fileRoot = createTreeFromJSON(fileSystemJSON)
        orgRoot = createTreeFromJSON(organizationJSON)
        # render
        self.fileTree.setRoot(fileRoot)
        self.orgTree.setRoot(orgRoot)
        # add selection listeners
        # def on_file_select(e): js.console.log('File selected:', e.detail.treeElement.presentation.getPresentableText())
        # self.fileTree.addEventListener('nodeSelect', create_proxy(on_file_select))
        # def on_org_select(e): js.console.log('Person/Department selected:', e.detail.treeElement.presentation.getPresentableText())
        # self.orgTree.addEventListener('nodeSelect', create_proxy(on_org_select))
