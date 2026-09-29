export const ExecutionAnalysisRunning = () => {
    return (
        <div className="flex flex-1 flex-col grow min-h-screen bg-gray-100 w-full min-w-[320px]">
            <div className="flex-1 p-6 space-y-8 flex justify-center items-center">
                <div className='bg-white p-6 rounded-lg shadow-lg w-full max-w-md'>
                    <p className="text-base">The risk detection analysis is running, please wait.</p>
                    <div className="flex justify-center mt-4">
                        <svg className="animate-spin h-8 w-8 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                    </div>
                </div>
            </div>
        </div>
    )
}