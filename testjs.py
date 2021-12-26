from bond import make_bond


class JavaScriptFile():
    def __init__(self, path):
        self.bond = make_bond('JavaScript')
        self.PATH = path
        self.__code = self.__get_code()
        self.bond.eval_block(self.__code)

    def __get_code(self):
        outp = ''
        with open(self.PATH) as file:
            for row in file:
                outp += row + '\n'
        return outp

    def call_func(self, name):
        self.bond.call(name)


if __name__ == '__main__':
    notion_api = JavaScriptFile('js/notion-api.js')
    notion_api.call_func('print_dio')
