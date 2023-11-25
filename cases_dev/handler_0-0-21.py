

def handler(get_score, tot_score, status):
    stat = status[0]
    score = 0.0
    details = []
    if stat.count('response string: ') > 0 and stat.count(', ans:') > 0:
        response_str = stat[stat.find('response string: ') + len('response string: '): stat.find(', ans:')]
        if response_str.count('navigator.clipboard.writeText') > 0:
            details.append('main match')
            score += 2.0
        if response_str.count('.select()') > 0 and response_str.count('document.execCommand("copy");') > 0:
            details.append('sub match')
            score += 1.0
    return (min(score, 2.0), 2.0, details)