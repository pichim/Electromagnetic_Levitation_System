function autoclean()
% AUTOCLEAN Checks the current directory and deletes:
% - All *.asv, *.slxc, *.slcx, *.bak, *.rt-win64, *.rxw64 files
% - All folders ending with _quarc_win64 or __sldrt_win64
% - The folder "slprj"
%
% Works platform-independently.

    fprintf('   --- autoclean ---\n');

    % Define file patterns to delete (files only)
    filePatterns = { ...
        '*.asv', ...
        '*.slxc', ...
        '*.slcx', ...
        '*.bak', ...
        '*.rt-win64', ...
        '*.rxw64' ...
    };

    % Loop through each pattern and delete matching files
    for i = 1:length(filePatterns)
        files = dir(filePatterns{i});
        for k = 1:length(files)
            delete(fullfile(files(k).folder, files(k).name));
            fprintf('   Deleted file: %s\n', fullfile(files(k).folder, files(k).name));
        end
    end

    % Handle directories ending with *_quarc_win64
    dirPatterns = { ...
        '*_quarc_win64', ...     % existing
        '*_sldrt_win64' ...     % NEW
    };

    for p = 1:length(dirPatterns)
        dirs = dir(dirPatterns{p});
        for k = 1:length(dirs)
            if dirs(k).isdir
                rmdir(fullfile(dirs(k).folder, dirs(k).name), 's'); % Recursive deletion
                fprintf('   Deleted directory: %s\n', fullfile(dirs(k).folder, dirs(k).name));
            end
        end
    end

    % Delete 'slprj' folder if it exists
    if isfolder('slprj')
        rmdir('slprj', 's');
        fprintf('   Deleted folder: slprj\n');
    end

end
