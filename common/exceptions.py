class QPSError(Exception):
    """
    QPS自定义异常
    """
    def __init__(self, info):
        self.info = info

    def __str__(self):
        return self.info
