
def handle(response):
    if response.count('console.log(this.newIds)') * response.count('});') > 0:
        if response.find('console.log(this.newIds)') < response.find('});'):
            return (1.0, 1.0, 'good')
        return (0.0, 1.0, 'all found but wrong placement')
    return (0.0, 1.0, 'keywords not found')