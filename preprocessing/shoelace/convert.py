import inspect
import json
from pathlib import Path
from typing import List

from wwwpy.common.designer import element_library as el
from wwwpy.common.designer.element_library import element_library
from wwwpy.common.rpc import serialization


def main():
    jet_json, vsc_json = load_jsons()

    assert len(jet_json) == len(vsc_json)

    elements: list[el.ElementDef] = []
    for jet, vsc in zip(jet_json, vsc_json):
        element = create_element(jet, vsc)
        elements.append(element)

    element_defs = serialization.to_json(elements, List[el.ElementDef])
    print(element_defs)
    restored = serialization.from_json(element_defs, List[el.ElementDef])
    json_file_root = Path(inspect.getfile(element_library)).parent
    (json_file_root / 'el_shoelace.json').write_text(element_defs)


def create_element(jet, vsc):
    tag_name = jet['name']
    assert tag_name == vsc['name']
    help_url = vsc['references'][0]['url']
    help = el.Help(jet['description'], help_url)
    attributes: list[el.AttributeDef] = []
    for jet_attr, vsc_attr in zip(jet['attributes'], vsc['attributes']):
        attr_name = jet_attr['name']
        assert attr_name == vsc_attr['name']
        jet_value = jet_attr.get('value')
        jet_default = jet_value.get('default')
        jet_type = jet_value.get('type')
        is_bool = jet_type == 'boolean'
        values = [] if is_bool else [dic['name'] for dic in (vsc_attr['values'])]

        attr = el.AttributeDef(
            attr_name,
            help=el.Help('', jet_attr.get('description', ''))
            , values=values, boolean=is_bool, default_value=jet_default
        )

        attributes.append(attr)

    events: list[el.EventDef] = []
    for jet_event in jet['events']:
        event_name = jet_event['name']
        event = el.EventDef(event_name, help=el.Help('', jet_event.get('description', '')))
        events.append(event)

    element = el.ElementDef(tag_name, 'js.HTMLElement', help=help,
                            attributes=attributes, events=events)
    return element


def load_jsons():
    par = parent()
    jetbrains_file = par / 'web-types.json'
    vscode_file = par / 'vscode.html-custom-data.json'
    jet_json = load(jetbrains_file)['contributions']['html']['elements']
    vsc_json = load(vscode_file)['tags']
    return jet_json, vsc_json


def parent():
    return Path(__file__).parent


def load(file):
    return json.loads(file.read_text())


if __name__ == '__main__':
    main()
