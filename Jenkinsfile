pipeline {
    agent { label 'python' }
    environment {
        // build specifics
        AUTO = "True"
        GIT_ACCOUNT = "ramongarciamx"
        GIT_URL = "ssh://git@codeberg.org/${GIT_ACCOUNT}"
        PYTHON = "python3"
        SOURCE = "rgarciamx"
        VENV_DIR = ".venv"
        // project specifics
        BASE_URL = "https://${GIT_ACCOUNT}.codeberg.page"
        DEST = "./pages"
        SRC = "./${SOURCE}"
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
                    python build_blog.py -s # s flag so we scan for foul language
                '''
            }

        }
        stage('Publish') {
            steps {
                sh '''
                    . ${VENV_DIR}/bin/activate
                    cd pages
                    git add -A
                    git commit -am \"Published from Jenkins on $(date +%Y-%m-%sT%H:%M:%S)\"
                    git push origin master
                '''
            }
        }
    }
    post {
        failure {
            cleanWs()
        }
        cleanup {
            dir("${SOURCE}") { deleteDir() }
            dir("pages") { deleteDir() }
        }
    }
}
