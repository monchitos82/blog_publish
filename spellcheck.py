from neuspell import BertChecker

checker = BertChecker()
checker.from_pretrained()

if __name__ == "__main__":
    filename = sys.argv[1]

    try:
        with open(filename) as f:
            content = f.read()
            if content:
                print(checker.correct(content))
    except IOError:
        log.error(f"File {filename} could not be read")
