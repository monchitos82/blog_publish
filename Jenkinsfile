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
            name: 'CLEAN_REPOSITORIES', 
            defaultValue: true, 
            description: 'Preserve the existing repositories in the workspace'
        )
    }
    stages {
        stage('Setup Environment') {
            steps {
                script {
                    def uvExists = fileExists '/home/jenkins/.local/bin/uv'
                    if (!uvExists || params.FORCE_SETUP) {
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
                script {
                    if (params.CLEAN_REPOSITORIES) {
                        dir("${SOURCE}") { deleteDir() }
                        dir("pages") { deleteDir() }
                        sh '''
                            git clone ${GIT_URL}/${SOURCE}
                            git clone ${GIT_URL}/pages
                        '''
                    } else {
                        if (fileExists("/home/jenkins/agent/workspace/blog/${SOURCE}")) {
                            sh '''
                            cd ${SOURCE}
                            git pull
                            cd ..
                            '''
                        } else {
                            sh '''
                            git clone ${GIT_URL}/${SOURCE}
                            '''
                        }
                        if (fileExists("/home/jenkins/agent/workspace/blog/pages")) {
                            sh '''
                            cd pages
                            git pull
                            cd ..
                            '''
                        } else {
                            sh '''
                            git clone ${GIT_URL}/pages
                            '''
                        }
                    }
                }
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
            echo 'Upon failure you should clean repositories for the next run!'
            cleanWs()
        }
        cleanup {
            script {
                if (params.CLEAN_REPOSITORIES) {
                    dir("${SOURCE}") { deleteDir() }
                    dir("pages") { deleteDir() }
                }
            }
        }
    }
}
