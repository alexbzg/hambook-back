from jinja2 import Environment, select_autoescape, PackageLoader

class HTMLTemplatesService:

    def __init__(self):
        self._env = Environment(
            loader=PackageLoader('app', 'templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def template(self, name: str):
        return self._env.get_template(f"{name}.html")

