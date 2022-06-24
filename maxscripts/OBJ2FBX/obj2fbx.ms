resetmaxfile #noPrompt
fn sLibGetAllFilesInDir inputDir rec type = 
(
	a = #( )
	dirsToProcess = #( inputDir )
	for dir in dirsToProcess do
	( 
		currentFiles = getFiles ( dir + "*." + ( type as string ) )
		for i in currentFiles do append a i
		if rec == true then
		(
			subDirs = getDirectories ( dir + "*.*" )
			for i in subDirs do append dirsToProcess i
		)
	)
	return a
)
root = getsavepath caption:"Select Source Path"
if root != undefined then (
	objFiles = sLibGetAllFilesInDir root true "OBJ"
	for i = 1 to objFiles.count do (
		f = objFiles[i]
		importFile f #noPrompt using:Wavefront_Object
		max select all
		fbxPath = ( getFilenamePath f ) + ( getFilenameFile f ) + ".FBX"
		exportFile fbxPath #noPrompt selectedonly:true using:FBXEXP
		resetmaxfile #noPrompt
	)
	messagebox ( "OK!" )
)