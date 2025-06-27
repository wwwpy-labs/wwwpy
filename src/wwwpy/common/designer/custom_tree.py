import js
from pyodide.ffi import create_proxy

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js


# Representation of item display properties
class ItemPresentation:
    def __init__(self, text, icon=None, backgroundColor=None):
        self.text = text
        self.icon = icon
        self.backgroundColor = backgroundColor

    def getPresentableText(self):
        return f"{self.icon} {self.text}" if self.icon else self.text

    def getBackgroundColor(self):
        return self.backgroundColor


# Tree node model with lazy child loading and rendering
class TreeElement:
    def __init__(self, presentation: ItemPresentation, child_loader, parent=None):
        self.presentation = presentation
        self.child_loader = child_loader
        self.parent = parent
        self.nodeDiv = None
        self.contentDiv = None
        self.children = None

    @property
    def level(self):
        return self.parent.level + 1 if self.parent else 0

    def getChildren(self):
        if self.children is None:
            self.children = self.child_loader()
        return self.children

    def hasChildren(self):
        return len(self.getChildren()) > 0

    def getNodeFragment(self, default_template):
        frag = default_template.content.cloneNode(True)
        self.nodeDiv = frag.querySelector('[data-id="node"]')
        self.contentDiv = frag.querySelector('[data-id="content"]')
        return frag

    def toggle(self):
        childrenDiv = self.nodeDiv.querySelector('.tree-node-children')
        toggleBtn = self.nodeDiv.querySelector('.tree-node-toggle')
        expanded = childrenDiv.classList.contains('expanded')
        if expanded:
            childrenDiv.classList.replace('expanded', 'collapsed')
            toggleBtn.classList.remove('expanded')
        else:
            childrenDiv.classList.replace('collapsed', 'expanded')
            toggleBtn.classList.add('expanded')

    def render(self, default_template, tree_instance, container):
        frag = self.getNodeFragment(default_template)
        self.nodeDiv.dataset.level = self.level
        hasKids = self.hasChildren()
        btn = frag.querySelector('[data-id="toggle-btn"]')
        btn.classList.toggle('leaf', not hasKids)
        if hasKids:
            childrenDiv = frag.querySelector('[data-id="children-container"]')
            childrenDiv.className = 'tree-node-children collapsed'

            def on_toggle(e):
                e.stopPropagation()
                if not childrenDiv.hasChildNodes():
                    for c in self.getChildren():
                        c.render(default_template, tree_instance, childrenDiv)
                self.toggle()

            btn.addEventListener('click', create_proxy(on_toggle))
        textSpan = frag.querySelector('[data-id="text"]')
        textSpan.textContent = self.presentation.getPresentableText()
        self.contentDiv.style.paddingLeft = f"{self.level * 20 + 8}px"
        bg = self.presentation.getBackgroundColor()
        if bg:
            self.contentDiv.style.backgroundColor = bg

        def on_select(ev):
            tree_instance.selectNode(self.contentDiv, self)

        self.contentDiv.addEventListener('click', create_proxy(on_select))
        container.appendChild(frag)


# Web component for rendering a tree
class CustomTree(wpc.Component, tag_name='custom-tree'):
    def init_component(self):
        # attach shadow and template
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        self.element.shadowRoot.innerHTML = """
        <style id="tree-style">
            :host { display: block; }
            .tree-node { margin: 0; user-select: none; }
            .tree-node-content { display: flex; align-items: center; padding: 2px; font-size: 12px; width: 100%; box-sizing: border-box; border-radius: 4px; }
            .tree-node-content:hover { background-color: #2E436E; }
            .tree-node-content.selected { background-color: #1f6feb !important; color: #ffffff; }
            .tree-node-toggle { width: 16px; height: 16px; margin-right: 4px; border: none; background: none; font-size: 12px; display: flex; align-items: center; justify-content: center; color: #8b949e; }
            .tree-node-toggle:hover { color: #e6edf3; }
            .tree-node-toggle .toggle-icon { display: flex; align-items: center; justify-content: center; width: 16px; height: 16px; }
            .tree-node-toggle.expanded .toggle-icon { transform: rotate(90deg); }
            .tree-node-toggle.leaf { visibility: hidden; }
            .tree-node-text { flex: 1; padding: 2px 4px; }
            .tree-node-children { margin-left: 0; overflow: auto; }
            .tree-node-children.collapsed { max-height: 0; }
            .tree-node-children.expanded { max-height: 1000px; }
        </style>
        <template id="default-tree-node-template">
            <div class="tree-node" data-id="node" data-level="">
                <div class="tree-node-content" data-id="content">
                    <button class="tree-node-toggle" data-id="toggle-btn">
                        <span class="toggle-icon" data-id="toggle-icon">
                            <!-- Copyright 2000-2022 JetBrains s.r.o. and contributors. Use of this source code is governed by the Apache 2.0 license. -->
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                              <path d="M6 11.5L9.5 8L6 4.5" stroke="#B4B8BF" stroke-linecap="round"/>
                            </svg>
                        </span>
                    </button>
                    <span class="tree-node-text" data-id="text"></span>
                </div>
                <div class="tree-node-children" data-id="children-container"></div>
            </div>
        </template>
        <div id="tree-container"></div>
        """
        self.container = self.element.shadowRoot.getElementById('tree-container')
        self.default_template = self.element.shadowRoot.getElementById('default-tree-node-template')
        self.root = None
        self.selectedNode = None

    def setRoot(self, root: TreeElement):
        self.root = root
        self.container.innerHTML = ''
        if root:
            root.render(self.default_template, self, self.container)

    def selectNode(self, contentDiv, treeElement):
        if self.selectedNode:
            self.selectedNode.classList.remove('selected')
        contentDiv.classList.add('selected')
        self.selectedNode = contentDiv
        self.element.dispatchEvent(js.CustomEvent.new(
            'nodeSelect',
            dict_to_js({'detail': {'treeElement': treeElement}})
        ))
