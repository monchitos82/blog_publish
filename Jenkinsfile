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
                script {
                    def uvExists = sh(script: "command -v uv", returnStatus: true) == 0
                    def forceSetup = env.FORCE_SETUP?.toBoolean()

                    if (!uvExists || forceSetup) {
                        echo "Installing or updating uv..."
                        sh '''
                            curl -LsSf https://astral.sh/uv/install.sh | sh
                            # Ensure the local bin is available for the rest of this block
                            export PATH="$HOME/.local/bin:$PATH"
                            uv sync --frozen
                        '''
                    } else {
                        echo "uv is already installed, skipping setup."
                    }
                }
            }
        }
        stage('Setup Sources') {
            steps {
                sh '''
                    git clone ${GIT_URL}/${SOURCE} # clone my sources
                    git clone ${GIT_URL}/pages # clone the destination repository
                    find ./pages -name '*.html' -delete
                '''
            }

        }
        stage('Build') {
            steps {
                sh '''
                    $HOME/.local/bin/uv run build_blog.py
                '''
            }

        }
        stage('Publish') {
            steps {
                catchError (buildResult: 'NOT_BUILT', stageResult: 'FAILURE', message: 'Failed to update pages'){
                    sh '''
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
