class Stack:
    def __init__(self):
        self.stackArray = [None] * 0
        self.topIndex = -1

    def push(self, item):
        self.topIndex = self.topIndex + 1
        self.stackArray[self.topIndex] = item

    def pop(self):
        if self.topIndex < 0:
            return None

        item = self.stackArray[self.topIndex]
        self.topIndex = self.topIndex - 1
        return item

    def peek(self):
        if self.topIndex < 0:
            return None

        return self.stackArray[self.topIndex]

q = Stack()
q.push(10)
q.push(20)

print(q.peek())