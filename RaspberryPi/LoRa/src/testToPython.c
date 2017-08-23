#include "python3.4/Python.h"

static PyObject *spam_system(PyObject *self, PyObject *args){
	const char *command;
	int sts;
	
	if(!PyArg_ParseTuple(args, "s", &command))
		return NULL;
	sts = system(command);
	
	return PyLong_FromLong(sts);
}

static PyMethodDef SpamMethods[] = {
	{"system", spam_system, METH_VARARGS, "Execute a shell command"},
	{NULL, NULL, 0, NULL} /*sentinel*/
};

static struct PyModuleDef spammodule = {
		PyModuleDef_HEAD_INIT,
		"spam",
		NULL,
		-1,
		SpamMethods
};

PyMODINIT_FUNC
PyInit_spam(void)
{
	return PyModule_Create(&spammodule);
}

int main(int argc, char *argv[])
{
	/* Add a built-in module, before Py_Initialize */
	PyImport_AppendInittab("spam", PyInit_spam);
	
	/* Pass argv[0] to the Python interpreter */
	Py_SetProgramName(argv[0]);
	
	/* Initialize the Python Interpreter. Required */
	Py_Initialize();
	
	/* Optionaly import the module */
	PyImport_ImportModule("spam");
}
