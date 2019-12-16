import os


PROJECTSDIR = 'Projects'
SRCDIR = 'src'
HEADERDIR = 'header'
CPPDIR = 'cpp'
OBJDIR = 'obj'

def find_headers(project_name):
    included_files = []
    project_dir = PROJECTSDIR + '/' + project_name + '/'

    header_path = project_dir + SRCDIR + '/' + HEADERDIR
    header_files = [header_path + '/' + header_name for header_name in os.listdir(header_path)]
    main_file = []
    macro = "#include"
    if 'main.cpp' in os.listdir(project_dir + SRCDIR + '/' + CPPDIR):
        main_file.append(project_dir + SRCDIR + '/' + CPPDIR + '/main.cpp')

    files_list = header_files + main_file
    for f_name in files_list:
        with open(f_name, 'r') as f:
            for line in f:
                if macro in line and not('<' in line): # system header are ignored
                    # getting rid of ""
                    included_files.append(line.split('"')[1])
    return(included_files)


def get_all_project_headers(project_name):
    projects_dirs = [dir.path for dir in os.scandir(PROJECTSDIR) if os.path.isdir(dir) and dir.name != project_name ]
    header_files = {}
    for project_path in projects_dirs:
        header_path = project_path + '/' + SRCDIR + '/' + HEADERDIR
        for header in os.listdir(header_path):
            header_files[header] = project_path
    return(header_files)

def get_includes_from_projects(project_name):
    my_headers = find_headers(project_name)
    project_headers = get_all_project_headers(project_name)
    header_from_other_projects = {}

    for header in my_headers:
        if header in project_headers:
            header_from_other_projects[header] = project_headers[header].split("\\")[-1] # project name

    return(header_from_other_projects)

def get_dependency_rules(project_name):
    includes = get_includes_from_projects(project_name)
    # returning call to makes as a list of str
    make_calls = []
    obj_files = []
    for entry in includes:
        obj_file = entry.split('.')[0] + '.o'
        obj_files.append("../" + PROJECTSDIR + '/' + includes[entry] + '/' + OBJDIR + '/' + obj_file)
        make_call = "cd teensy3 && make " + "../" + PROJECTSDIR + '/' + includes[entry] + '/' + OBJDIR + '/' + obj_file + " PROJECTNAME=" + includes[entry]
        make_calls.append(make_call)

    return(make_calls,obj_files)






if __name__ == "__main__":
    print(find_headers('Anchor_c'))
    print(get_all_project_headers('Anchor_c'))
    print(get_dependency_rules('Anchor_c'))
