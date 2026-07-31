pipeline {
    agent { label 'python' }
    environment {
        VENV_DIR = ".venv"
        PYTHON = "python3"
        SOURCE = "rgarciamx"
        BASE_URL = "https://rgarciamx.codeberg.page"
        SRC = "../rgarciamx"
        DEST = "../pages"
        YEAR_LOOKBACK = 2
    }
    stages {
        stage('Setup Environment') {
            steps {
                sh '''
                    $PYTHON -m venv $VENV_DIR
                    . $VENV_DIR/bin/activate
                    pip install --upgrade pip setuptools wheel
                    pip install -r requirements.txt
                '''
            }
        }
        stage('Build') {
            steps {
                sh '''
                    . $VENV_DIR/bin/activate
                    git clone $SOURCE # clone my sources
                    git clone pages # clone the destination repository
                    python build_blog.py
                    cd -
                '''
            }
        }
        stage('Scan Foul Language') {
            steps {
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh '''
                        export AUTO="true"
                        . $VENV_DIR/bin/activate
                        python build_blog.py -s
                    '''
                }
            }
        }
        stage('Publish') {
            steps {
                sh '''
                    . $VENV_DIR/bin/activate
                    cd pages
                    git add -A
                    git commit -am "Published from Jenkins on $(date +%Y-%m-%sT%H:%M:%S)"
                    git push origin master
                '''
            }
        }
    }
}
