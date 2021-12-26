import bond


class JavaScriptFile():
    def __init__(self, path):
        self.bond = bond.make_bond('JavaScript')
        self.PATH = path
        self.__code = self.__get_code()
        try:
            self.bond.eval_block(self.__code)
        except bond.RemoteException as e:
            print(f'JS [{self.PATH}]: {e.error}')

    def __get_code(self):
        outp = ''
        with open(self.PATH) as file:
            for row in file:
                outp += row + '\n'
        return outp

    def run(self, name, args=None):
        try:
            self.bond.call(name, args)
        except bond.RemoteException as e:
            print(f'JS [{self.PATH}]: {e.error}')

    def interpritate(self, code):
        self.bond.eval(code)

    def define(self, name):
        return self.bond.callable(name)


if __name__ == '__main__':
    notion_api = JavaScriptFile('js/notion-api.js')
    add_item = notion_api.run('addItem', 'new')
