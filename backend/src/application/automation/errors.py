class AutomationLocationNotFoundError(LookupError):
    pass


class AutomationRuleNotFoundError(LookupError):
    pass


class AutomationContextError(ValueError):
    pass
