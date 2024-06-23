import React, { useState } from 'react';
import { Tabs, Tab, IconButton, Box } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import AddIcon from '@mui/icons-material/Add';
import MenuIcon from '@mui/icons-material/Menu';
import NoteDoc from './NoteDoc';
import TabPanel from './TabPanel';
import DrawerComponent from './DrawerComponent';

const TabsComponent: React.FC = () => {
  const [tabs, setTabs] = useState([{ id: 0, title: 'Untitled' }]);
  const [value, setValue] = useState(0);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const handleChange = (event: React.ChangeEvent<{}>, newValue: number) => {
    setValue(newValue);
  };

  const handleAddTab = () => {
    const newTab = { id: tabs.length, title: `Untitled` };
    setTabs([...tabs, newTab]);
    setValue(tabs.length);
  };

  const handleDeleteTab = (tabIndex: number) => {
    const newTabs = tabs.filter((tab, index) => index !== tabIndex);
    setTabs(newTabs);
    setValue(tabIndex > 0 ? tabIndex - 1 : 0);
  };

  const toggleDrawer = (open: boolean) => {
    setDrawerOpen(open);
  };

  const handleTitleChange = (index: number, title: string) => {
    const newTitle = title.trim() === "" ? "Untitled" : title;
    const newTabs = tabs.map((tab, tabIndex) => 
      tabIndex === index ? { ...tab, title: newTitle } : tab
    );
    setTabs(newTabs);
  };

  return (
    <div className="w-full">
      <Box display="flex" alignItems="center">
        <IconButton onClick={() => toggleDrawer(true)}>
          <MenuIcon />
        </IconButton>
        <Tabs value={value} onChange={handleChange} aria-label="NoteDoc Tabs">
          {tabs.map((tab, index) => (
            <Tab
              key={tab.id}
              label={
                <div className="flex items-center">
                  {tab.title}
                  {tabs.length > 1 && (
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteTab(index);
                      }}
                    >
                      <CloseIcon fontSize="small" />
                    </IconButton>
                  )}
                </div>
              }
            />
          ))}
          <IconButton onClick={handleAddTab}>
            <AddIcon />
          </IconButton>
        </Tabs>
      </Box>
      {tabs.map((tab, index) => (
        <TabPanel key={tab.id} value={value} index={index}>
          <NoteDoc noteId={`note-${tab.id}`} onTitleChange={(title) => handleTitleChange(index, title)} />
        </TabPanel>
      ))}
      <DrawerComponent open={drawerOpen} onClose={() => toggleDrawer(false)} />
    </div>
  );
}

export default TabsComponent;
