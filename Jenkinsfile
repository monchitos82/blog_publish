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
    parameters {
        booleanParam(
            name: 'FORCE_SETUP', 
            defaultValue: false, 
            description: 'Force a fresh installation of uv and sync environment'
        )
        booleanParam(
            name: 'KEEP_REPOSITORIES', 
            defaultValue: false, 
            description: 'Preserve the existing repositories in the workspace'
        )
    }
    stages {
        stage('Setup Environment') {
            steps {
                script {
                    def uvExists = fileExists '/home/jenkins/.local/bin/uv'
                    if (!uvExists || env.FORCE_INSTALL) {
                        sh '''
                            curl -LsSf https://astral.sh/uv/install.sh | sh
                            export PATH="$HOME/.local/bin:$PATH"
                            uv sync --frozen
                        '''
                    }
                }
            }
        }
        stage('Setup Sources') {
            steps {
                sh '''
                    git clone ${GIT_URL}/${SOURCE} # clone my sources
                    git clone ${GIT_URL}/pages # clone the destination repository
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
            script {
                if (!env.KEEP_REPOSITORIES) {
                    dir("${SOURCE}") { deleteDir() }
                    dir("pages") { deleteDir() }
                }
            }
        }
    }
}
