pipeline {
    agent { label 'python' }
    environment {
        // build specifics
        VENV_DIR = ".venv"
        PYTHON = "python3"
        SOURCE = "rgarciamx"
        GIT_ACCOUNT = "ramongarciamx"
        GIT_URL = "ssh://git@codeberg.org/${GIT_ACCOUNT}"
        // project specifics
        BASE_URL = "https://${GIT_ACCOUNT}.codeberg.page"
        SRC = "./${SOURCE}"
        DEST = "./pages"
        YEAR_LOOKBACK = 2
    }
    stages {
        stage('Setup Environment') {
            steps {
                sh '''
                    ${PYTHON} -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip setuptools wheel
                    pip install -r requirements.txt
                '''
            }
        }
        stage('Build') {
            steps {
                sh '''
                    . ${VENV_DIR}/bin/activate
                    git clone ${GIT_URL}/${SOURCE} # clone my sources
                    git clone ${GIT_URL}/pages # clone the destination repository
                    python build_blog.py
                '''
            }
        }
        stage('Scan Foul Language') {
            steps {
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh '''
                        export AUTO="true"
                        . ${VENV_DIR}/bin/activate
                        python build_blog.py -s
                    '''
                }
            }
        }
        stage('Publish') {
            steps {
                sh '''
                    . ${VENV_DIR}/bin/activate
                    cd pages
                    git add -A
                    git commit -am "Published from Jenkins on $(date +%Y-%m-%sT%H:%M:%S)"
                    git push origin master
                '''
            }
        }
    }
    post {
        failure {
            cleanWs()
        }
    }
}
