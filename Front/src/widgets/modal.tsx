import { Dialog } from "primereact/dialog";
import { FilterTable } from "./filterTable";

export const Modal: React.FC<{ endpoint: string, title:string, filter:any, visible:boolean, setVisible:(value:boolean)=>void, session:(value:boolean)=>void }> = ({ endpoint, title, filter, visible, setVisible, session }) => {
  return (
    <Dialog
      header={filter?`${title}: ${filter}`:`${title}`}
      visible={visible}
      blockScroll={false}
      className="shadow-2xl bg-white dark:bg-gray-900 text-gray-900 dark:text-white rounded-lg p-0 min-w-[320px] max-w-[80%] min-h-[500px] max-h-[80%]"
      contentClassName="flex min-h-[100%] max-h-[100%] w-full"
      pt={{
        header: { className: "text-sm text-black px-6 pb-0 pt-4" },
        headerTitle: { className: "whitespace-nowrap truncate" }
      }}
      onHide={() => {if (!visible) return; setVisible(false); }}
      modal
    >
      <div className="flex flex-1">
        <FilterTable endpoint={endpoint} filter={filter} session={session}></FilterTable>
      </div>
    </Dialog>    
  );
};