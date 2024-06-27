from typing import List


class branch_c:

    functions: List['branch_function'] = []

    def __init__(self, filename):
        self.file = open(f"coverage report {filename}", "a")
        self.fileName = filename
        pass

    def reportAll(self, functions: List['branch_function']):
        self.file.write(f"-=-=-=-coverage report for: {self.fileName}-=-=-=-\n")
        for fun in functions:
            fun.report()
        self.file.write(f"-=-=-=--=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n\n")

    def contains_member_with_value(self, value : str):
        for obj in self.functions:
            if obj.name == value:
                return True
        return False
    
    def flatten_functions(self, functions: List['branch_function']) -> List['branch_function']:
        return_functions = []
        while len(functions) != 0:
            indices_to_remove: List[int] = [0]
            working_function: 'branch_c.branch_function' = functions[0]
            for i in range(1,len(functions)):
                if functions[0].name == functions[i].name:
                    indices_to_remove.append(i)
                    for key, value in functions[i].flagMap.items():
                        if key in working_function.flagMap:
                            working_function.flagMap[key] += value
                        else:
                            working_function.flagMap[key] = value
            return_functions.append(working_function)
            for index in sorted(indices_to_remove, reverse=True):
                functions.pop(index)
        return return_functions
    
    def __del__(self):
        functions_to_report = self.flatten_functions(self.functions)
        self.reportAll(functions_to_report)

    class branch_function:

        def __init__(self, parent: 'branch_c', name: str, totalFlags: int):
            self.parent = parent
            self.name = name
            self.totalFlags = totalFlags
            self.flagMap : dict[str, int] = {}
            self.parent.functions.append(self)
            pass

        def addFlag(self, number: str):
            if not number in self.flagMap:
                self.flagMap[number] = 1
            else:
                self.flagMap[number] += 1
        
        def report(self):
            for key, value in self.flagMap.items():
                self.parent.file.write(f"{key}: {value}\n")
            if self.totalFlags != 0:
                self.parent.file.write(f"total branch coverage for {self.name}: {(len(self.flagMap) / self.totalFlags) * 100}%\n\n")
            else:
                self.parent.file.write(f"no branches in this function: {self.name}\n\n")
                