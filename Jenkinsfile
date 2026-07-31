pipeline {
    agent { label 'python' }
    environment {
        // build specifics
        GIT_ACCOUNT = "ramongarciamx"
        GIT_URL = "ssh://git@codeberg.org/${GIT_ACCOUNT}"
        SOURCE = "rgarciamx"
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
                    curl -LsSf https://astral.sh/uv/install.sh | sh
                    export PATH="$HOME/.local/bin:$PATH"
                    uv sync --frozen
                '''
            }
        }
        stage('Build') {
            steps {
                sh '''
                    git clone ${GIT_URL}/${SOURCE} # clone my sources
                    git clone ${GIT_URL}/pages # clone the destination repository
                    uv run build_blog.py
                '''
            }

        }
        stage('Publish') {
            steps {
                catchError (buildResult: 'NOT_BUILT', stageResult: 'FAILURE', message: 'Failed to update pages'){
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
