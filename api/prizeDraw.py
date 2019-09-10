"""
抽奖算法
作者：York
"""
import random


class randomMachine(object):

    def setWeight(self, data):
        self.data = data

    def drawing(self):

        total = sum(self.data.values())
        # print(total)
        rad = random.random()*total

        cur_total = 0
        res = ""
        for k, v in self.data.items():
            cur_total += v
            if rad <= cur_total:
                res = k
                break
        return res


if __name__ == "__main__":
    test = randomMachine()
    test.setWeight({"1": 0.01, "2": 0.04, "3": 0.05, "4": 0.1, "5": 0.15, "6": 0.15, "7": 0.2, "8": 0.3})
    target = 0
    testNo = 1000000
    for i in range(testNo):
        result = test.drawing()
        if result == "8":
            target += 1
    per = target/testNo
    # print(per)
