class UnknownOperatorError(Exception):
    def __init__(self, message: str | None = None, *, operator: str | None = None):
        if message is None:
            message = (
                f"Unknown operator '{operator}'. "
                "Make sure you registered it via SuffixSet.register_suffix(...)"
            )
        super().__init__(message)
        self.operator = operator
